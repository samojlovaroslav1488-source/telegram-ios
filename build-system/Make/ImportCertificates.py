import os
import sys
import argparse
import subprocess


def sh(args, check=False):
    r = subprocess.run(['security'] + args, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    print('[security {}] exit={}'.format(args[0], r.returncode))
    if out:
        print(out[:1500])
    if check and r.returncode != 0:
        sys.exit(1)
    return r.stdout


def import_certificates(certificatesPath):
    if not os.path.exists(certificatesPath):
        print('{} does not exist'.format(certificatesPath))
        sys.exit(1)

    keychain_name = 'temp.keychain'
    keychain_password = 'secret'

    sh(['delete-keychain', keychain_name])
    sh(['create-keychain', '-p', keychain_password, keychain_name], check=True)

    existing = sh(['list-keychains', '-d', 'user'])
    existing = [l.strip().strip('"') for l in existing.splitlines() if l.strip()]
    sh(['list-keychains', '-d', 'user', '-s', keychain_name] + existing)

    sh(['set-keychain-settings', keychain_name])
    sh(['unlock-keychain', '-p', keychain_password, keychain_name])

    print('FILES:', sorted(os.listdir(certificatesPath)))
    for file_name in sorted(os.listdir(certificatesPath)):
        file_path = certificatesPath + '/' + file_name
        if file_path.endswith('.p12') or file_path.endswith('.cer'):
            print('IMPORT', file_name)
            sh(['import', file_path, '-k', keychain_name, '-P', '',
                '-T', '/usr/bin/codesign', '-T', '/usr/bin/security'])

    print('IMPORT WWDR')
    sh(['import', 'build-system/AppleWWDRCAG3.cer', '-k', keychain_name,
        '-P', '', '-T', '/usr/bin/codesign', '-T', '/usr/bin/security'])

    sh(['set-key-partition-list', '-S', 'apple-tool:,apple:',
        '-k', keychain_password, keychain_name])

    sh(['find-identity', '-p', 'codesigning', keychain_name])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='build')
    parser.add_argument('--path', required=True, help='Path to certificates.')
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    import_certificates(args.path)
