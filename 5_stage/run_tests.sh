#!/bin/bash


echo ">>> Тест 1: Этап 5 – команды chown и vfs-load"
echo "Проверка работы команд изменения владельца и загрузки VFS..."
echo "Запуск скрипта startup_test6.txt..."
python3 5_stage.py --vfs vfs_test2.xml --startup startup_test6.txt
echo ""
echo ""

echo ">>> Тест 2: Этап 5 – интерактивные проверки chown"
echo "Тестирование команды chown на разных файлах и директориях..."
python3 5_stage.py --vfs vfs_test2.xml
echo ""
echo ""

echo ">>> Тест 3: Этап 5 – проверка vfs-load"
echo "Тестирование загрузки нескольких файлов VFS подряд..."
python3 5_stage.py --vfs vfs_test1.xml
echo ""
echo ""

echo "=========================================="
echo " Все тесты Этапа 5 завершены."
echo "=========================================="
