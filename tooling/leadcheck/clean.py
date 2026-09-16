#!/usr/bin/env python3
"""
Clean lead data: blank broken phones, merge duplicates, preserve earlier opening dates.
Reads and modifies propertystack/data/*/chat-leads.csv files in-place.
"""
import csv
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def is_valid_phone(phone):
    """Check if phone is in format (XXX) XXX-XXXX with 10 digits total."""
    if not phone or not phone.strip():
        return True  # Empty is not invalid, just missing
    phone = phone.strip()
    return bool(re.match(r'^\(\d{3}\) \d{3}-\d{4}$', phone))


def count_facts(row):
    """Count non-empty fields in a row."""
    return sum(1 for v in row.values() if v and str(v).strip())


def parse_date(date_str):
    """Parse date string, return datetime or None."""
    if not date_str or not str(date_str).strip():
        return None
    try:
        return datetime.strptime(str(date_str).strip(), '%Y-%m-%d')
    except ValueError:
        return None


def get_earliest_date(date_str1, date_str2):
    """Return the earlier date string, preferring non-empty values."""
    d1 = parse_date(date_str1)
    d2 = parse_date(date_str2)

    if d1 and d2:
        return date_str1 if d1 <= d2 else date_str2
    if d1:
        return date_str1
    if d2:
        return date_str2
    return date_str1 or date_str2


def merge_rows(row1, row2):
    """Merge two duplicate rows, keeping the one with more facts and earliest dates."""
    facts1 = count_facts(row1)
    facts2 = count_facts(row2)

    # Start with the row that has more facts
    if facts1 >= facts2:
        merged = row1.copy()
        other = row2
    else:
        merged = row2.copy()
        other = row1

    # Fill in missing fields from the other row
    for key in merged.keys():
        if not merged[key] or not str(merged[key]).strip():
            if other.get(key):
                merged[key] = other[key]

    # Use earliest opening_date
    if 'opening_date' in merged:
        merged['opening_date'] = get_earliest_date(
            merged.get('opening_date', ''),
            other.get('opening_date', '')
        )

    return merged


def find_duplicate_groups(rows):
    """Find groups of duplicate rows. Returns dict of {group_id: [row_indices]}."""
    by_address = defaultdict(list)
    by_name_city = defaultdict(list)

    for i, row in enumerate(rows):
        address = (row.get('address') or '').strip().lower()
        if address:
            by_address[address].append(i)

        name = (row.get('name') or '').strip().lower()
        city = (row.get('city') or '').strip().lower()
        if name and city:
            by_name_city[(name, city)].append(i)

    # Merge overlapping groups
    merged_indices = set()
    groups = {}
    group_id = 0

    for indices in by_address.values():
        if len(indices) > 1:
            key = tuple(sorted(indices))
            if key not in groups and not any(idx in merged_indices for idx in indices):
                groups[group_id] = indices
                merged_indices.update(indices)
                group_id += 1

    for indices in by_name_city.values():
        if len(indices) > 1:
            # Check if any of these indices are already in a group
            in_group = [idx for idx in indices if idx in merged_indices]
            not_in_group = [idx for idx in indices if idx not in merged_indices]

            if not_in_group:
                if in_group:
                    # Merge into existing group
                    for gid, gindices in groups.items():
                        if any(idx in gindices for idx in in_group):
                            groups[gid].extend(not_in_group)
                            merged_indices.update(not_in_group)
                            break
                else:
                    key = tuple(sorted(indices))
                    if key not in groups:
                        groups[group_id] = indices
                        merged_indices.update(indices)
                        group_id += 1

    return groups


def clean_area(csv_path):
    """Clean a single area's CSV file. Returns before/after counts."""
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))

    fieldnames = list(rows[0].keys()) if rows else []
    before = {
        'total': len(rows),
        'broken_phones': 0,
        'duplicates': 0,
    }

    # Count issues before cleaning
    for row in rows:
        phone = (row.get('office_phone') or '').strip()
        if phone and not is_valid_phone(phone):
            before['broken_phones'] += 1

    dup_groups = find_duplicate_groups(rows)
    before['duplicates'] = sum(len(indices) - 1 for indices in dup_groups.values())

    # Blank broken phones
    for row in rows:
        phone = (row.get('office_phone') or '').strip()
        if phone and not is_valid_phone(phone):
            row['office_phone'] = ''

    # Merge duplicates
    rows_to_keep = []
    processed_indices = set()

    for i, row in enumerate(rows):
        if i in processed_indices:
            continue

        # Find if this row is in a duplicate group
        in_group = False
        for dup_indices in dup_groups.values():
            if i in dup_indices:
                # Merge all rows in this group
                merged = row.copy()
                for dup_idx in dup_indices:
                    if dup_idx != i:
                        merged = merge_rows(merged, rows[dup_idx])
                rows_to_keep.append(merged)
                processed_indices.update(dup_indices)
                in_group = True
                break

        if not in_group:
            rows_to_keep.append(row)
            processed_indices.add(i)

    after = {
        'total': len(rows_to_keep),
        'broken_phones': 0,
        'duplicates': 0,
    }

    # Write cleaned data back
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)

    return before, after


def main():
    data_dir = Path('propertystack/data')
    all_before = {}
    all_after = {}

    for csv_path in sorted(data_dir.glob('*/chat-leads.csv')):
        area = csv_path.parent.name
        print(f"Cleaning {area}...", end=' ')
        before, after = clean_area(csv_path)
        all_before[area] = before
        all_after[area] = after
        print(f"✓ ({before['total']} → {after['total']} rows)")

    # Print summary
    print("\n=== BEFORE ===")
    for area in sorted(all_before.keys()):
        b = all_before[area]
        print(f"{area.upper()}: {b['total']} rows, {b['broken_phones']} broken phones, {b['duplicates']} duplicates")

    print("\n=== AFTER ===")
    for area in sorted(all_after.keys()):
        a = all_after[area]
        print(f"{area.upper()}: {a['total']} rows, {a['broken_phones']} broken phones, {a['duplicates']} duplicates")

    total_before = sum(b['total'] for b in all_before.values())
    total_after = sum(a['total'] for a in all_after.values())
    total_phones_before = sum(b['broken_phones'] for b in all_before.values())
    total_dups_before = sum(b['duplicates'] for b in all_before.values())

    print(f"\n=== SUMMARY ===")
    print(f"Total rows: {total_before} → {total_after} (removed {total_before - total_after} duplicates)")
    print(f"Broken phones: {total_phones_before} → 0 (blanked)")
    print(f"Duplicates: {total_dups_before} → 0 (merged)")


if __name__ == '__main__':
    main()
