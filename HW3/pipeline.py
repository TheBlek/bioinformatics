from prefect import flow, task, get_run_logger
from prefect.artifacts import create_link_artifact
import utils
import subprocess
import os
import sys

# Define a base directory for output files for better organization
OUTPUT_DIR = "prefect_output"

@task
def bwa_index(fasta_file: str):
    """Indexes the reference genome using bwa index."""
    logger = get_run_logger()
    cmd = f"bwa index {fasta_file}"
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    logger.info(result.stdout)
    if result.stderr:
        logger.warning(f"Stderr: {result.stderr}")
    return fasta_file # Return the path for downstream tasks

@task
def fastqc_analysis(fastq_file: str, output_dir: str):
    """Runs FastQC on the raw sequencing data."""
    logger = get_run_logger()
    os.makedirs(output_dir, exist_ok=True)
    cmd = f"fastqc {fastq_file} -o {output_dir}"
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    logger.info(result.stdout)
    if result.stderr:
        logger.warning(f"Stderr: {result.stderr}")
    # The FastQC output HTML will be named after the input file, e.g., SRR33672046_fastqc.html
    base_name = os.path.basename(fastq_file).replace(".fastq.gz", "_fastqc.html")
    report_path = os.path.join(output_dir, base_name)
    # Rename to a generic name for consistency
    final_report_path = os.path.join(output_dir, "fastqc_report.html")
    os.rename(report_path, final_report_path)
    logger.info(f"FastQC report moved to {final_report_path}")
    create_link_artifact(
        key="fastqc-report",
        link=f"file://{os.path.abspath(final_report_path)}",
        description="FastQC quality report for raw sequencing data."
    )
    return final_report_path

@task
def bwa_mem(fasta_file: str, fastq_file: str, output_sam: str):
    """Performs read alignment using bwa mem."""
    logger = get_run_logger()
    cmd = f"bwa mem -t 10 {fasta_file} {fastq_file} > {output_sam}"
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=True) # stdout redirected to file, so no capture_output
    logger.info(f"Alignment complete, output saved to {output_sam}")
    return output_sam

@task
def samtools_view(input_sam: str, output_bam: str):
    """Converts SAM to BAM using samtools view."""
    logger = get_run_logger()
    cmd = f"samtools view -S -b {input_sam} > {output_bam}"
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=True)
    logger.info(f"SAM converted to BAM, output saved to {output_bam}")
    return output_bam

@task
def extract_percent_from_flagstat(bam_file: str):
    """
    Runs samtools flagstat and pipes its output to a Python script.
    Handles potential failure of the Python script gracefully.
    """
    logger = get_run_logger()
    flagstat_cmd = f"samtools flagstat {bam_file}"
    logger.info(f"Running: {flagstat_cmd}")
    result = subprocess.run(flagstat_cmd, shell=True, check=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Flagstat failed.")
        logger.error(f"Stdout: {result.stdout}")
        logger.error(f"Stderr: {result.stderr}")
        raise
    percent = utils.extract_mapped_percentage(result.stdout)
    if percent is None:
        logger.error("Failed to parse out mapped percentage")
        raise
    if percent < 90:
        logger.error(f"Mapped percentage was too low: {percent}")
        raise

@task
def samtools_sort(input_bam: str, output_sorted_bam: str):
    """Sorts BAM file using samtools sort."""
    logger = get_run_logger()
    cmd = f"samtools sort {input_bam} > {output_sorted_bam}"
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=True)
    logger.info(f"BAM file sorted, output saved to {output_sorted_bam}")
    return output_sorted_bam

@task
def gunzip_fasta(gzipped_fasta: str, unzipped_fasta: str):
    """Decompresses the gzipped FASTA file."""
    logger = get_run_logger()
    cmd = f"gunzip -c {gzipped_fasta} > {unzipped_fasta}"
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=True)
    logger.info(f"FASTA file unzipped to {unzipped_fasta}")
    return unzipped_fasta

@task
def freebayes_variant_calling(fasta_file: str, sorted_bam: str, output_vcf: str):
    """Performs variant calling using Freebayes."""
    logger = get_run_logger()
    # Ensure freebayes is in PATH or provide full path
    freebayes_cmd = "freebayes"
    cmd = f"{freebayes_cmd} -f {fasta_file} {sorted_bam} > {output_vcf}"
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=True)
    logger.info(f"Variant calling complete, report saved to {output_vcf}")
    return output_vcf

@flow(name="Genomics Pipeline")
def genomics_pipeline(
    ref_fasta_gz: str = "hg38.fa.gz",
    fastq_read: str = "SRR33672046.fastq.gz"
):
    """
    A Prefect pipeline for genomics analysis including alignment, QC, and variant calling.
    """
    logger = get_run_logger()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info(f"Ensured output directory '{OUTPUT_DIR}' exists.")

    ref_fasta_unzipped = os.path.join(OUTPUT_DIR, "hg38.fa")
    output_sam = os.path.join(OUTPUT_DIR, "out.sam")
    output_bam = os.path.join(OUTPUT_DIR, "out.bam")
    output_sorted_bam = os.path.join(OUTPUT_DIR, "out.sorted.bam")
    bayes_report_vcf = os.path.join(OUTPUT_DIR, "bayes_report.vcf")

    # Flow definition
    # These tasks can start as soon as their inputs are available
    # and if the TaskRunner supports parallelism.

    # bwa_index and fastqc_analysis can run in parallel if the runner allows.
    # bwa_index outputs 'indexed_fasta' which bwa_mem needs.
    # fastqc_analysis outputs 'fastqc_html_report' which no other task needs as an input file.
    indexed_fasta_future = bwa_index.submit(ref_fasta_gz) # Submit to run as soon as possible
    fastqc_report_future = fastqc_analysis.submit(fastq_read, OUTPUT_DIR) # Submit to run as soon as possible

    # bwa_mem needs the output of bwa_index. We await the future.
    aligned_sam_future = bwa_mem.submit(indexed_fasta_future, fastq_read, output_sam)

    # All subsequent tasks depend on the outputs of the alignment stream
    converted_bam_future = samtools_view.submit(aligned_sam_future, output_bam)
    percent_extracted_future = extract_percent_from_flagstat.submit(converted_bam_future)
    sorted_bam_future = samtools_sort.submit(output_sorted_bam, converted_bam_future, wait_for=[percent_extracted_future])
    unzipped_fasta_future = gunzip_fasta.submit(ref_fasta_gz, ref_fasta_unzipped)

    # freebayes_variant_calling needs the output of sorted_bam and unzipped_fasta.
    # We await both futures.
    vcf_report_future = freebayes_variant_calling.submit(unzipped_fasta_future, sorted_bam_future, bayes_report_vcf)

    # Retrieve results at the end of the flow if needed for final logging
    # Note: Awaiting here doesn't block the *submission* of tasks, only the retrieval of their results.
    # The tasks themselves will have already run in parallel if the runner supports it.
    indexed_fasta_path = indexed_fasta_future.result()
    fastqc_html_report_path = fastqc_report_future.result()
    aligned_sam_path = aligned_sam_future.result()
    converted_bam_path = converted_bam_future.result()
    percent_extracted_value = percent_extracted_future.result()
    sorted_bam_path = sorted_bam_future.result()
    unzipped_fasta_path = unzipped_fasta_future.result()
    vcf_report_path = vcf_report_future.result()


    logger.info("\nPipeline execution complete!")
    logger.info(f"Final VCF report: {vcf_report_path}")
    logger.info(f"FastQC report: {fastqc_html_report_path}")
    if percent_extracted_value:
        logger.info(f"Extracted percentage from flagstat: {percent_extracted_value}")

if __name__ == "__main__":
    # Run the Prefect flow
    if len(sys.argv) >= 3:
        genomics_pipeline(sys.argv[1], sys.argv[2])
    elif len(sys.argv) >= 2:
        genomics_pipeline(sys.argv[1])
    else:
        genomics_pipeline()
