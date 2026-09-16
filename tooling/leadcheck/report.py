#!/usr/bin/env python3
"""
Lead data quality report: flags broken phones, duplicate projects, missing units, and invalid links.
Reads propertystack/data/*/chat-leads.csv and saves tooling/leadcheck/report.md
"""
import csv
import re
from pathlib import Path
from collections import defaultdict

def is_valid_phone(phone):
    """Check if phone is in format (XXX) XXX-XXXX with 10 digits total."""
    if not phone or not phone.strip():
        return True  # Empty is not invalid, just missing
    phone = phone.strip()
    # Must match exactly (XXX) XXX-XXXX format
    return bool(re.match(r'^\(\d{3}\) \d{3}-\d{4}$', phone))

def is_valid_link(url):
    """Check if URL is http(s) or empty."""
    if not url or not url.strip():
        return True  # Empty is OK
    url = url.strip()
    return url.startswith('http://') or url.startswith('https://')

def extract_digits(phone):
    """Extract just the digits from a phone number."""
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    return digits if len(digits) == 10 else None

def get_area_from_path(path):
    """Extract area name from path like propertystack/data/tx/chat-leads.csv"""
    return path.parent.name

def find_duplicates(rows):
    """Find duplicate projects: exact street address + same city only.

    Name alone (including placeholder names like "Unnamed project") never
    triggers a match; only rows with an address can be duplicates.
    """
    by_address_city = defaultdict(list)
    for i, row in enumerate(rows):
        address = re.sub(r'\s+', ' ', (row['address'] or '').strip().lower())
        city = re.sub(r'\s+', ' ', (row['city'] or '').strip().lower())
        if address:
            by_address_city[(address, city)].append(i)

    dup_pairs = set()
    for indices in by_address_city.values():
        if len(indices) > 1:
            for idx in indices:
                dup_pairs.add(idx)

    return dup_pairs

def main():
    data_dir = Path('propertystack/data')
    report_path = Path('tooling/leadcheck/report.md')

    results = {}
    all_rows = []

    # Load all data
    for csv_path in sorted(data_dir.glob('*/chat-leads.csv')):
        area = get_area_from_path(csv_path)
        with open(csv_path) as f:
            rows = list(csv.DictReader(f))
            results[area] = {
                'total': len(rows),
                'broken_phones': [],
                'duplicates': [],
                'missing_units': [],
                'invalid_links': [],
            }
            all_rows.extend([(area, i, row) for i, row in enumerate(rows)])

    # Find issues
    for area, csv_path in sorted((get_area_from_path(p), p) for p in data_dir.glob('*/chat-leads.csv')):
        with open(csv_path) as f:
            rows = list(csv.DictReader(f))

        # Broken phones
        for i, row in enumerate(rows):
            phone = (row['office_phone'] or '').strip()
            if phone and not is_valid_phone(phone):
                results[area]['broken_phones'].append({
                    'index': i,
                    'name': row['name'],
                    'city': row['city'],
                    'phone': phone,
                })

        # Missing units
        for i, row in enumerate(rows):
            units = (row['units'] or '').strip()
            if not units:
                results[area]['missing_units'].append({
                    'index': i,
                    'name': row['name'],
                    'city': row['city'],
                })

        # Invalid links
        for i, row in enumerate(rows):
            for link_field in ['permit_link', 'news_link', 'website_link', 'agenda_link', 'map_link']:
                url = (row.get(link_field) or '').strip()
                if url and not is_valid_link(url):
                    results[area]['invalid_links'].append({
                        'index': i,
                        'field': link_field,
                        'name': row['name'],
                        'url': url,
                    })

        # Duplicates (by address or name+city)
        dup_indices = find_duplicates(rows)
        for idx in dup_indices:
            row = rows[idx]
            results[area]['duplicates'].append({
                'index': idx,
                'name': row['name'],
                'city': row['city'],
                'address': row['address'],
            })

    # Write report
    with open(report_path, 'w') as f:
        f.write("# Lead Data Quality Report\n\n")

        # Summary
        total_broken = sum(len(r['broken_phones']) for r in results.values())
        total_dups = sum(len(r['duplicates']) for r in results.values())
        total_missing = sum(len(r['missing_units']) for r in results.values())
        total_invalid = sum(len(r['invalid_links']) for r in results.values())

        f.write(f"**Summary:** {total_broken} broken phones, {total_dups} duplicates, {total_missing} missing units, {total_invalid} invalid links\n\n")

        # Per-area breakdown
        for area in sorted(results.keys()):
            r = results[area]
            f.write(f"## {area.upper()}\n")
            f.write(f"- Total rows: {r['total']}\n")
            f.write(f"- Broken phones: {len(r['broken_phones'])}\n")
            f.write(f"- Duplicates: {len(r['duplicates'])}\n")
            f.write(f"- Missing units: {len(r['missing_units'])}\n")
            f.write(f"- Invalid links: {len(r['invalid_links'])}\n")

            # Broken phones examples
            if r['broken_phones']:
                f.write(f"\n### Broken phones (up to 10)\n")
                for item in r['broken_phones'][:10]:
                    f.write(f"- {item['name']}, {item['city']}: `{item['phone']}`\n")

            # Duplicates examples
            if r['duplicates']:
                f.write(f"\n### Duplicates (up to 10)\n")
                for item in r['duplicates'][:10]:
                    f.write(f"- {item['name']}, {item['city']} @ {item['address']}\n")

            # Missing units examples
            if r['missing_units']:
                f.write(f"\n### Missing units (up to 10)\n")
                for item in r['missing_units'][:10]:
                    f.write(f"- {item['name']}, {item['city']}\n")

            # Invalid links examples
            if r['invalid_links']:
                f.write(f"\n### Invalid links (up to 10)\n")
                for item in r['invalid_links'][:10]:
                    f.write(f"- {item['name']}: {item['field']} = `{item['url']}`\n")

            f.write("\n")

    # Print summary to console
    print(f"✓ Broken phones: {total_broken}")
    print(f"✓ Duplicates: {total_dups}")
    print(f"✓ Missing units: {total_missing}")
    print(f"✓ Invalid links: {total_invalid}")
    print(f"\nReport saved to {report_path}")

if __name__ == '__main__':
    main()
