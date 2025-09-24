from Bio import SeqIO
import os
import argparse

def generate_egfr_subdomain_fasta(input_fasta, output_fasta, start_residue, end_residue):
    if not os.path.exists(input_fasta):
        raise FileNotFoundError(f"Input FASTA not found: {input_fasta}")

    # Load full-length sequence
    record = SeqIO.read(input_fasta, "fasta")
    full_seq = str(record.seq)

    # Adjust for 0-based indexing
    truncated_seq = full_seq[start_residue - 1:end_residue]

    # Update record
    record.seq = truncated_seq
    record.id = f"{record.id}_res{start_residue}_{end_residue}"
    record.description = f"Subdomain residues {start_residue}-{end_residue}"

    # Write to output
    SeqIO.write(record, output_fasta, "fasta")
    print(f"✅ Truncated FASTA saved to: {output_fasta}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subdomain from a FASTA protein sequence.")
    parser.add_argument("--input", required=True, help="Path to input FASTA file")
    parser.add_argument("--output", required=True, help="Path to output truncated FASTA")
    parser.add_argument("--start", type=int, required=True, help="Start residue (1-based index)")
    parser.add_argument("--end", type=int, required=True, help="End residue (1-based index, inclusive)")
    args = parser.parse_args()

    generate_egfr_subdomain_fasta(args.input, args.output, args.start, args.end)
