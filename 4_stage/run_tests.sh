#!/bin/bash
echo ">>> Тест 1: Этап 4 – команды wc и history"
echo "Проверка новых команд на стандартном VFS..."
echo "Запуск скрипта startup_test5.txt..."
python3 4_stage.py --vfs vfs_test2.xml --startup startup_test5.txt
echo ""
echo ""

echo ">>> Тест 2: Этап 4 – интерактивные проверки wc"
echo "Тестирование работы wc на разных типах файлов..."
python3 4_stage.py --vfs vfs_test3.xml
echo ""
echo ""

echo ">>> Тест 3: Этап 4 – проверка history"
echo "Проверка сохранения истории после нескольких команд..."
python3 4_stage.py --vfs vfs_test2.xml --startup startup_test4.txt
echo ""
echo ""

echo "=========================================="
echo " Все тесты Этапа 4 завершены."
echo "=========================================="
