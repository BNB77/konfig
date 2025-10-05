#!/bin/bash

echo "=========================================="
echo " Тестирование Shell Emulator – Этап 3 (VFS)"
echo "=========================================="
echo ""

echo ">>> Тест 1: Минимальный VFS (vfs_test1.xml)"
echo "Проверка структуры с одним файлом..."
python3 3_stage.py --vfs vfs_test1.xml
echo ""
echo ""

echo ">>> Тест 2: Стандартный VFS + стартовый скрипт"
echo "Запуск многопутевого VFS со скриптом startup_test4.txt..."
python3 3_stage.py --vfs vfs_test2.xml --startup startup_test4.txt
echo ""
echo ""

echo ">>> Тест 3: Глубокая структура VFS (3+ уровней)"
echo "Проверка вложенных директорий..."
python3 3_stage.py --vfs vfs_test3.xml
echo ""
echo ""

echo ">>> Тест 4: Отсутствующий файл VFS"
echo "Проверка обработки ошибки при отсутствии файла..."
python3 3_stage.py --vfs nonexistent_vfs.xml
echo ""
echo ""

echo ">>> Тест 5: Некорректный XML"
echo "Проверка обработки ошибки при повреждённом XML..."
echo "invalid xml content" > invalid_test.xml
python3 3_stage.py --vfs invalid_test.xml
rm -f invalid_test.xml
echo ""
echo ""

echo "=========================================="
echo " Все тесты завершены."
echo "=========================================="
