const u16 size = 4096;

u8* str;

str = __ir__syscall(9,0,size,3,0x22,-1,0);

loop:
{
    __ir__syscall(0,0,str,size);
    __ir__syscall(1,1,str,size);
}
goto loop:

__ir__syscall(60,0);