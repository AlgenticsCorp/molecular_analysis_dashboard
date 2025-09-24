import pandas as pd
import json
import sys

# Usage: python parse_mutations.py input_file.tsv > mutations.json
if len(sys.argv) != 2:
    print("Usage: python parse_mutations.py <mutation_data.tsv>", file=sys.stderr)
    sys.exit(1)

input_path = sys.argv[1]

# Read the mutation file (TSV format from cBioPortal)
df = pd.read_csv(input_path, sep='\t')

# Filter for EGFR mutations of patient P-0076655
egfr_mutations = (
    df[(df['Sample ID'].str.contains('P-0076655')) &
       (df['Gene'] == 'EGFR') &
       (df['Protein Change'].notna())]
    ['Protein Change']
    .unique()
    .tolist()
)

# Output mutations.json structure
mutation_json = {
    "gene": "EGFR",
    "mutations": egfr_mutations
}

print(json.dumps(mutation_json, indent=2))
