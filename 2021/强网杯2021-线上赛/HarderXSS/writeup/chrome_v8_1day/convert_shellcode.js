var shellcode = "\x90\x90"; // replace with shellcode
while(shellcode.length % 4)
	shellcode += "\x90";

var buf = new ArrayBuffer(shellcode.length);
var arr = new Uint32Array(buf);
var u8_arr = new Uint8Array(buf);

for(var i=0;i<shellcode.length;++i)
	u8_arr[i] = shellcode.charCodeAt(i);

console.log(String(arr));