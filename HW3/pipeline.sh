#!/usr/bin/env sh

# Can be run in background until bwa mem
bwa index hg38.fa.gz

fastqc SRR33672046.fastq.gz

mv SRR33672046_fastqc.html fastqc_report.html

bwa mem -t 10 hg38.fa.gz SRR33672046.fastq.gz > out.sam

samtools view -S -b out.sam > out.bam

# python extract_percent.py could fail e.g. exit with code 1
samtools flagstat out.bam | python extract_percent.py 

samtools sort out.bam > out.sorted.bam

gunzip hg38.fa.gz

freebayes-1.3.6-linux-amd64-static -f hg38.fa out.sorted.bam > bayes_report.vcf
