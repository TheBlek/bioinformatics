Illumina HiSeq/MiSeq/NextSeq/NovoSeq pair-end \w bwa mem \w Prefect

## Инструкция по установке
Для запуска данного пайплайна в пути должны быть следующие бинарники:
- samtools
- bwa
- fastqc
- gunzip
- freebayes

### Установка Prefect:
```
pip install prefect
curl -LsSf https://astral.sh/uv/install.sh | sh # Install `uv`.
uvx prefect-cloud login # Installs `prefect-cloud` into a temporary virtual env.
```

## Инструкция по запуску

`uv run pipeline.py <genom.fa.gz> <reads.fastq.gz>`

Входные файлы:
    референсный геном - первый параметр в командной строке, hg38.fa.gz по-дефолту
    риды - второй параметр в командной строке, SRR33672046.fastq.gz иначе

После запуска в командной строке будет ссылка для просмотра статуса пайплайна.
