#!/bin/bash

echo "Тест 1"
python 2_stage.py

echo ""
echo "Тест 2"
python 2_stage.py --vfs /tmp/test_vfs

echo ""
echo "Тест 3"
python 2_stage.py --startup nonexistent.txt

echo ""
echo "Тест 4"
python 2_stage.py --startup startup_test1.txt

echo ""
echo "Тест 5"
python 2_stage.py --vfs /tmp/vfs --startup startup_test2.txt

echo ""
echo "Тест 6"
python 2_stage.py --vfs /tmp/vfs --startup startup_test3.txt


echo ""
echo "Все тесты завершены!"