# Вводные
Последовательность белка: MKGMLTGPVTILNWSWPREDITHEEQTKQLALAIRDEVLDLEAAGIKIIQIDEAALREKLPLRKSDWHAKYLDWAIPAFRLVHSAVKPTTQIHTHMCYSE

Инструменты фолдинга: ESMFold, OpenFold

Парное выравнивание: должно было быть http://bioinfo3d.cs.tau.ac.il/MultiProt/php.php, но у меня этот сайт не открывается (пытался месяц наверно, с момента выдачи ДЗ), поэтому взял jCE-CP здесь - https://www.rcsb.org/alignment

# Результаты
Ноутбуки с результатами: [OpenFold](openfold.ipynb), [ESMFold](esmfold.ipynb)

OpenFold ноутбук вызвал проблемы, последнюю из которых (несоответствие версии драйверов нвидиа) не получилось решить.
Пришлось найти сайт, который вычислял OpenFold фолдинг за меня.

pdb результаты: [OpenFold](openfold.pdb), [ESMFold](esmfold.pdb)

[Результат выравнивания](alignment_res.zip)

<img title="Результат выравнивания" alt="Результат выравниванияя" src="alignment.png">

По картинке видно, что общая структура белков очень похожая получилась. Думаю, результатам можно доверять.