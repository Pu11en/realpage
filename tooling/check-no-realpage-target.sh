#!/bin/bash
# Check for RealPage-as-target (customer/pitch) references.
# BLOCK: RealPage positioned as our target customer/sales prospect or project identifier
# ALLOW: RealPage as a software brand in data, vendor lists, research documentation

set -e

VIOLATIONS=()

# Files/patterns that are entirely safe (archive, tests, data, or being removed)
SAFE_PATTERNS=(
    "propertystack/data/"
    "^archive/"
    "/done/"
    "/tests/"
    "test_"
    "TEST-"
    "SPOT-CHECK"
    "^docs/plans/"
    "^docs/.*research\.md$"
    "site/ai-visibility.html$"
    "ai_visibility_lawsuit.py$"
    "casestudy/"
    "rules\.json$"
    "leads\.json$"
)

# Files to scan
SCAN_DIRS=(
    "site/"
    "chatbot/"
    "README.md"
    "AGENTS.md"
    "docs/"
    "marketing-board/"
    "business/"
)

is_safe_path() {
    local file="$1"
    for pattern in "${SAFE_PATTERNS[@]}"; do
        if [[ "$file" =~ $pattern ]]; then
            return 0
        fi
    done
    return 1
}

# Check if a specific line is a violation
# Returns 0 (true) if it's allowed, 1 (false) if it's a violation
is_allowed() {
    local file="$1"
    local line="$2"

    # ALLOW: Software vendor lists (VENDORS constant)
    if [[ "$line" =~ VENDORS ]]; then
        return 0
    fi

    # ALLOW: Color/styling/mapping for vendors (contains hex color like #f472b6)
    if [[ "$line" =~ \#[0-9a-f] ]]; then
        return 0
    fi

    # ALLOW: Python docstring lines (triple quotes)
    if [[ "$line" =~ '"""' ]]; then
        return 0
    fi

    # ALLOW: Lists of competitors (Yardi, Entrata, RealPage, etc.)
    if [[ "$line" =~ Yardi.*RealPage|RealPage.*Yardi|Entrata.*RealPage|AppFolio.*RealPage|RealPage.*Entrata ]]; then
        return 0
    fi

    # ALLOW: "and the like" / competitor context / rivals
    if [[ "$line" =~ "and the like\)|competing|rivals" ]]; then
        return 0
    fi

    # ALLOW: Outside-in research explanations
    if [[ "$line" =~ "no access to RealPage"|"outside-in only"|"Public-source evidence"|"Runners-up:" ]]; then
        return 0
    fi

    # ALLOW: Query/search documentation for features that query the data
    if [[ "$line" =~ "search.*RealPage|query.*RealPage|RealPage.*research.*folder" ]]; then
        return 0
    fi

    # ALLOW: Data format documentation
    if [[ "$file" =~ LEAD-FORMAT.md$ ]]; then
        return 0
    fi

    # ALLOW: Architecture/detector comments in code
    if [[ "$line" =~ "RealPage.*buildings.*data|client-map.*RealPage" ]]; then
        return 0
    fi

    # BLOCK: Target customer positioning ("for RealPage", "opportunities for RealPage")
    if [[ "$line" =~ "for RealPage" ]] || [[ "$line" =~ "opportunities for RealPage" ]] || [[ "$line" =~ "RealPage sales" ]]; then
        return 1
    fi

    # BLOCK: Project identifier in headers
    if [[ "$line" =~ "RealPage / PropertyStack" ]]; then
        return 1
    fi

    # BLOCK: Map/dashboard showing "RealPage already has clients" or filtering by RealPage
    if [[ "$line" =~ "Where RealPage already" ]] || [[ "$line" =~ "RealPage.*clients" ]] || [[ "$line" =~ "skip.*RealPage" ]]; then
        return 1
    fi

    # BLOCK: Internal coordination (Discord threads, etc.)
    if [[ "$line" =~ "RealPage.*Discord" ]] || [[ "$line" =~ "RealPage.*thread" ]]; then
        return 1
    fi

    # BLOCK: Site library and research features for RealPage
    if [[ "$line" =~ "RealPage.*library" ]] || [[ "$line" =~ "RealPage.*site.*library" ]]; then
        return 1
    fi

    # BLOCK: AI Visibility tied to RealPage
    if [[ "$line" =~ "about RealPage" && "$line" =~ "AI.*Visibility" ]] || [[ "$line" =~ "RealPage.*visibility" ]]; then
        return 1
    fi

    # DEFAULT: Block (assume it's a violation if not explicitly allowed)
    return 1
}

# Scan files
for dir in "${SCAN_DIRS[@]}"; do
    if [[ ! -e "$dir" ]]; then
        continue
    fi

    if [[ -d "$dir" ]]; then
        while IFS= read -r file; do
            [[ -z "$file" ]] && continue
            is_safe_path "$file" && continue

            while IFS= read -r linenum; do
                [[ -z "$linenum" ]] && continue
                line=$(sed -n "${linenum}p" "$file")

                if is_allowed "$file" "$line"; then
                    continue
                fi

                VIOLATIONS+=("$file:$linenum: $line")
            done < <(grep -n "RealPage" "$file" 2>/dev/null | cut -d: -f1)
        done < <(find "$dir" -type f \( -name "*.md" -o -name "*.html" -o -name "*.js" -o -name "*.py" \) 2>/dev/null)
    else
        # Single file
        while IFS= read -r linenum; do
            [[ -z "$linenum" ]] && continue
            line=$(sed -n "${linenum}p" "$dir")

            if is_allowed "$dir" "$line"; then
                continue
            fi

            VIOLATIONS+=("$dir:$linenum: $line")
        done < <(grep -n "RealPage" "$dir" 2>/dev/null | cut -d: -f1)
    fi
done

# Report
if [[ ${#VIOLATIONS[@]} -gt 0 ]]; then
    echo "Found RealPage-as-target references (should be archived or removed):"
    echo ""
    printf '%s\n' "${VIOLATIONS[@]}"
    echo ""
    echo "Total violations: ${#VIOLATIONS[@]}"
    exit 1
else
    echo "✓ No RealPage-as-target references found"
    exit 0
fi
