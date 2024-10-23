# Mortal-Blade
An attempt to automate PTH/PTP attack.
![image](https://github.com/user-attachments/assets/118c0fed-f48d-4ff2-9ad5-7ca809b0e04b)

The tool/Script is supposed to do following things:
- Take breached creds ie domain Username & Password
- Perform simple Crackmapexec gather pwned machines
- Perform secretsdump on each machine gathered, clean usernames/hashes and pass them further in network kinda like a recursive mode thing.
- Until Domain Controller is found/Compromised
- Save all output in .txt file

Ps. The tool is in beta and has only been tested in a personal AD environment.



