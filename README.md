# PS4 GTA V Native Updater
An IDA Pro script to update native addresses for new versions

## Purpose
Rockstar randomizes native hashes every GTA V version. Modding tools need these new hashes to determine what address to call for a given native function. This IDA script will generate `natives.h` for any new version of GTA V to be used in projects like [Native Caller](https://github.com/2much4u/PS4-GTA-V-Native-Caller) or [Menu Base](https://github.com/2much4u/PS4-GTA-V-Menu-Base). You can read more about what natives are and why they are useful in the `README` for [Native Caller](https://github.com/2much4u/PS4-GTA-V-Native-Caller).

## Usage
### 1. Load GTA V EBOOT into IDA Pro (7.0+)
### 2. Select File -> Script File and select this script
### 3. Select a crossmap file
A crossmap file is a text file representing a map from a previous GTA V version's native hashes to a new version's native hashes. These can commonly be found online with a quick Google search for any version of GTA V. The file format is expected to be:
```c
0xOLDHASH, 0xNEWHASH
0xOLDHASH2, 0xNEWHASH2
0xOLDHASH3, 0xNEWHASH3
...
```
### 4. Select the `registerNative` function
This is a function used in the game binary to register natives. You will need to find it yourself, but it is fairly easy to find. To find it, byte search with `ALT+B` in IDA for any of the new hashes in the crossmap file. Any hash will do besides `SYSTEM` natives. See more info on `SYSTEM` natives later. After searching for the byte pattern, you should come across a result that looks somewhat like this:
```
...
lea     rsi, sub_1065770            # native function
mov     rdi, 97C63D95072367BAh      # hash searched for
call    sub_228BC10                 # registerNative
lea     rdi, loc_1065260
call    nullsub_581
lea     rsi, loc_1065850            # native function
mov     rdi, 0AFEFADC285965BBEh     # native hash
call    sub_228BC10                 # registerNative
lea     rdi, sub_1065270
call    nullsub_581
lea     rsi, sub_1065870            # native function
mov     rdi, 89F38C325D9E03E7h      # native hash
call    sub_228BC10                 # registerNative
...
```
In this example, `sub_228BC10` is the registerNative function. That is the function you want to select when prompted by this script.
### 5. Select a natives header file
This is a clean `natives.h` downloaded from nativedb. You can always find the latest version of this at http://www.dev-c.com/nativedb/natives.h
### 6. That's it! The script is done
You should expect an output from IDA that looks somewhat like
```
Found 6166 natives in crossmap
Found 6160 natives in EBOOT
Merged 6140 natives in the maps
Failed to find address for 0xae3fee8709b39dcbL
Failed to find address for 0x64e630faf5f60f44L
Failed to find address for 0x7eec2a316c250073L
Failed to find address for 0x80e4a6eddb0be8d9L
Failed to find address for 0xa306f470d1660581L
Failed to find address for 0x966c2bc2a7fe3f30L
Failed to find address for 0x676ed266aadd31e0L
Failed to find address for 0x77faddcbe3499df7L
newHeader.h created
Unable to replace 8 natives
```
The file `newHeader.h` can be found in the same directory as your IDA database. The hex value `0xDEADBEEF` will put in place for any native this script is unable to find a function address for.
### 7. (Optional) Fix header for use in Native Caller
For use in my PS4 GTA V Native Caller, you will need to replace
```c
#include "types.h"
#include "nativeCaller.h"
```
in the `newHeader.h` output from this script with
```c
#include "invoker.h"
```
before replacing the file `PS4-GTA-V-Native-Caller/gtaPayload/include/natives.h`

## Notes about `SYSTEM` natives
Some crossmaps include `SYSTEM` natives and some do not. These natives do not change hashes across GTA V versions and are registered using a different function than the `registerNative` noted earlier. This script will automatically find this different registration function and find the `SYSTEM` natives using a hardcoded list of hashes.
