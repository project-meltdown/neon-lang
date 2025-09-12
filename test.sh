set -e

python protonc/main.py examples/simple.ne > test.asm
nasm -f elf64 -o test.o test.asm
ld test.o