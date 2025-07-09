@echo off
echo Iniciando Money Manager G5 Backend con Machine Learning
echo =======================================================

echo.
echo Activando entorno virtual...
call env\Scripts\activate

echo.
echo Verificando instalación de paquetes...
python -c "import fastapi, sqlalchemy, sklearn; print('✓ Dependencias instaladas correctamente')"

echo.
echo Para inicializar la base de datos ejecuta:
echo python init_setup.py

echo.
echo ¿Quieres iniciar el servidor ahora? (S/N)
set /p choice=

if /i "%choice%"=="S" (
    echo.
    echo Iniciando servidor en desarrollo...
    echo La documentación estará disponible en: http://localhost:8000/docs
    echo Presiona Ctrl+C para detener el servidor
    echo.
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
) else (
    echo.
    echo Para iniciar manualmente el servidor:
    echo uvicorn main:app --reload
    echo.
    echo La documentación estará disponible en:
    echo http://localhost:8000/docs
)

pause
