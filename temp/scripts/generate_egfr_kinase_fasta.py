from Bio import SeqIO
import os

def generate_egfr_kinase_domain_fasta(
    input_fasta="work/egfr_mutant.fasta",
    output_fasta="work/egfr_kinase_mutant.fasta",
    kinase_start=711,  # 1-based index in UniProt (residue 712)
    kinase_end=978     # inclusive
):
    if not os.path.exists(input_fasta):
        raise FileNotFoundError(f"Input FASTA not found: {input_fasta}")

    # Load full-length mutant sequence
    record = SeqIO.read(input_fasta, "fasta")
    full_seq = str(record.seq)

    # Adjust to 0-based Python indexing
    truncated_seq = full_seq[kinase_start:kinase_end]

    # Update record
    record.seq = truncated_seq
    record.id = record.id + "_kinase"
    record.description = f"EGFR kinase domain (residues {kinase_start+1}-{kinase_end})"

    # Save truncated sequence
    SeqIO.write(record, output_fasta, "fasta")
    print(f"✅ Kinase domain FASTA saved to: {output_fasta}")

if __name__ == "__main__":
    generate_egfr_kinase_domain_fasta()
