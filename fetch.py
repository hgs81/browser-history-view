import os
import sys
import json
import subprocess
from datetime import datetime

# parameters
exclude_domains = [
    'www.google.com',
    'localhost',
    '192.168.',
]
exclude_files = [
    # '*cjpalhdlnbpafiamejdnhcphjbkeiagm*',
    '*Extensions/cjpalhdlnbpafiamejdnhcphjbkeiagm*',    # uBlockOrigin
    '*Extensions/hdokiejnpimakedhajhdlcegeplioahd*',    # LastPass
    '*Extensions/nkbihfbeogaeaoehlefnkodbefgpgknn*',    # MetaMask
    '*IndexedDB/*.google.com*',
]
dry_run = False
run_mode = 'all'
dump_mode = False
dump_dir = 'backup'
delta = 86400   # defaults to 1d

from params import *
if os.getenv("DRY_RUN"):
    dry_run = True

FNULL = open(os.devnull, 'w')
BASEDIR = os.path.dirname(os.path.realpath(__file__))
DUMPDIR = os.path.join(BASEDIR, dump_dir)
if not os.path.exists(DUMPDIR):
    os.mkdir(DUMPDIR)
HBD = os.path.join(BASEDIR, 'hbd.exe' if sys.platform == 'win32' else 'hbd')
ZIP = os.path.join(BASEDIR, 'bin', 'zip.exe') if sys.platform == 'win32' else 'zip'


''' get home directory '''
def get_home_dir():
    return os.path.expanduser('~')

''' get list of backup files '''
def get_paths_to_zip(oftenChange = True, staticChange = True, extensionData = True, indexedDB = True, prefix = '', profile = 'Default'):
    list = []
    if oftenChange:
        list.extend([
            prefix + "Local State",
            prefix + profile + "/Preferences",
            prefix + profile + "/Secure Preferences",
            prefix + profile + "/History",
            prefix + profile + "/Favicons",
            prefix + profile + "/Cookies",
            prefix + profile + "/Web Data",
            prefix + profile + "/Shortcuts",
            prefix + profile + "/Visited Links",
            prefix + profile + "/Network Action Predictor",
            prefix + profile + "/QuotaManager",
            prefix + profile + "/Bookmarks",
            prefix + profile + "/Trusted Vault",
            prefix + profile + "/Custom Dictionary.txt",
            prefix + profile + "/PreferredApps",
            prefix + profile + "/Affiliation Database",
            prefix + profile + "/Media History",
            prefix + profile + "/Login Data",
            prefix + profile + "/Login Data For Account",
            prefix + profile + "/Extension Cookies",
            prefix + profile + "/Top Sites",
            prefix + profile + "/heavy_ad_intervention_opt_out.db",
            prefix + profile + "/Local Storage",
            prefix + profile + "/Local Extension Settings",
            prefix + profile + "/Network",
            prefix + profile + "/Site Characteristics Database",
            prefix + profile + "/Sync Data",
            prefix + profile + "/Extension State",
            prefix + profile + "/Shared_proto_db",
            prefix + profile + "/Managed Extension Settings",
            prefix + profile + "/blob_storage",
            prefix + profile + "/data_reduction_proxy_leveldb",
            prefix + profile + "/GCM Store",
            prefix + profile + "/Platform Notifications",
            prefix + profile + "/Sessions",
            prefix + profile + "/Session Storage"
        ])
    if staticChange:
        list.extend([
            prefix + profile + "/Accounts/",
            prefix + profile + "/AutofillStrikeDatabase/",
            prefix + profile + "/BudgetDatabase/",
            prefix + profile + "/coupon_db/",
            prefix + profile + "/databases/",
            prefix + profile + "/Download Service/",
            prefix + profile + "/Extension Rules/",
            prefix + profile + "/Extension Scripts/",
            prefix + profile + "/Feature Engagement Tracker/",
            prefix + profile + "/JumpListIconsMostVisited/",
            prefix + profile + "/optimization_guide_hint_cache_store/",
            prefix + profile + "/optimization_guide_model_and_features_store/",
            prefix + profile + "/Search Logos/",
            prefix + profile + "/Storage/",
            prefix + profile + "/Sync App Settings/",
            prefix + profile + "/Sync Extension Settings/",
            prefix + profile + "/VideoDecodeStats/",
            prefix + profile + "/Web Applications/",
            prefix + "First Run"
        ])
    if extensionData:
        list.append(prefix + profile + "/Extensions")
    if indexedDB:
        list.append(prefix + profile + "/IndexedDB")
    return list

''' list all google chrome profile directory '''
def list_chrome_profile(path = None):
    chrome_profile = []
    if not path:
        if sys.platform == 'darwin':
            path = os.path.join(get_home_dir(), 'Library', 'Application Support', 'Google', 'Chrome')
        elif sys.platform == 'linux':
            path = os.path.join(get_home_dir(), '.config', 'google-chrome')
        elif sys.platform == 'win32':
            path = os.path.join(os.environ.get('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            if 'History' in files:
                profile_name = os.path.basename(root)
                if profile_name in ['Default', 'System Profile', 'Guest Profile']:
                    continue
                chrome_profile.append(root)
    return chrome_profile

def list_incogniton_profile(path = None):
    incogniton_profile = []
    if not path:
        if sys.platform == 'darwin':
            path = os.path.join(get_home_dir(), 'Library', 'Application Support', 'Incogniton', 'config')
        elif sys.platform == 'win32':
            path = os.path.join(os.environ.get('APPDATA'), 'Incogniton', 'Incogniton', 'config')
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            if 'Default' in dirs:
                incogniton_profile.append(os.path.join(root, 'Default'))
    return incogniton_profile

''' list all history json file in specified path '''
def list_history_files(path):
    history_files = []
    if os.path.exists(path):
        for file in os.listdir(path):
            file_name = os.path.basename(file)
            if file_name.endswith('_history.json'):
                history_files.append(os.path.join(path, file))
    return history_files

''' get chrome profile path '''
def get_chrome_profile_path(index = 0):
    profile_path = None
    if sys.platform == 'darwin':
        profile_path = os.path.join(get_home_dir(), 'Library', 'Application Support', 'Google', 'Chrome', 'Profile ' + str(index) if index else 'Default')
    elif sys.platform == 'linux':
        profile_path = os.path.join(get_home_dir(), '.config', 'google-chrome', 'Profile ' + str(index) if index else 'Default')
    elif sys.platform == 'win32':
        profile_path = os.path.join(os.environ.get('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Profile ' + str(index) if index else 'Default')
    return profile_path
    
''' get chrome account info from preference file '''
def get_chrome_acc_info(profile_path):
    acc_info = {}
    pref_file = os.path.join(profile_path, 'Preferences')
    if os.path.isfile(pref_file):
        with open(pref_file, 'r') as f:
            try:
                pref_data = json.load(f)
                if 'account_info' in pref_data and len(pref_data['account_info']) > 0:
                    acc_info = pref_data['account_info'][0]
            except:
                pass
    return acc_info

''' get chromium account info from preference file '''
def get_chromium_acc_info(profile_path):
    acc_info = {}
    pref_file = os.path.join(profile_path, 'Preferences')
    if os.path.isfile(pref_file):
        with open(pref_file, 'r') as f:
            try:
                pref_data = json.load(f)
                if 'profile' in pref_data and len(pref_data['profile']) > 0:
                    acc_info['full_name'] = pref_data['profile']['name']
            except:
                pass
    return acc_info

''' add profile info and print to stdout '''
def add_profile_info(browser, profile = 'Default', acc_info = {}):
    full_name = acc_info.get('full_name')
    email = acc_info.get('email')
    profile_data.append({
        'browser': browser,
        'profile': profile,
        'full_name': full_name,
        'email': email
    })
    infostr = "%s | %s | %s | %s" % (browser, profile, full_name, email)
    return infostr

''' copy bookmarks, history, cookies, etc '''
def copy_files(browser, profile_path, output_dir):
    for file_name in ['Bookmarks', 'History', 'Cookies', os.path.join('Network', 'Cookies'), 'Login Data', 'Login Data For Account', 'Preferences', 'Secure Preferences']:
        file_path = os.path.join(profile_path, file_name)
        if os.path.exists(file_path):
            if sys.platform == 'win32':
                os.system('copy /y "%s" "%s/" >NUL' % (file_path, output_dir))
            else:
                os.system('cp "%s" "./%s/"' % (file_path, output_dir))
    
    key_file = os.path.join(BASEDIR, browser + 'Key')
    if os.path.exists(key_file):
        if sys.platform == 'win32':
            os.system('copy /y "%s" "%s/" >NUL' % (key_file, output_dir))
        else:
            os.system('cp "%s" "./%s/"' % (key_file, output_dir))

def zip_files(output_path, arg_list, comment = None, quiet = True):
    args = [ZIP, '-r', output_path]
    args.extend(arg_list)
    if quiet:
        args.append('-q')
    if comment:
        args.append('-z')
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate(input=comment.encode())[0]
        if output and not quiet:
            print(output.decode()[0:100])
    else:
        subprocess.call(args, stdout=FNULL, stderr=FNULL)

''' dump profile as a zip file '''
def dump_profile(profile_path, dump_prefix, comment = None):
    os.chdir(os.path.realpath(os.path.join(profile_path, '..')))
    profile_name = os.path.basename(profile_path)
    output_name = "%s_%s.zip" % (
        "".join(x for x in dump_prefix if x.isalnum() or x in "._-"),
        datetime.now().strftime("%Y%m%d%H%M%S")
    )
    args = get_paths_to_zip(profile=profile_name)
    for item in exclude_files:
        args.extend(['-x', item])
    print("Dumping profile %s as %s/%s ..." % (dump_prefix, dump_dir, output_name))
    zip_files(os.path.join(DUMPDIR, output_name), args, comment)
    os.chdir(BASEDIR)

def dump_results(comment = None):
    os.chdir(BASEDIR)
    output_name = "results_%s_%s.zip" % (
        "".join(x for x in os.getlogin() if x.isalnum() or x in "._-"),
        datetime.now().strftime("%Y%m%d%H%M%S")
    )
    print("Dumping results as %s/%s ..." % (dump_dir, output_name))
    zip_files(os.path.join(DUMPDIR, output_name), output_files, comment)

''' parse history json file '''
def parse_history_file(history_file, browser, profile = 'Default', acc_info = {}):
    if not os.path.exists(history_file):
        return
    with open(history_file, 'rb') as f:
        history_data = json.load(f)
        # print(history_data)
    if not history_data:
        return
    if dump_mode:
        return

    # sort history by date
    history_data.sort(key=lambda x: x['LastVisitTime'], reverse=True)

    # get history within delta time
    for history in history_data:
        # parse isodate string
        try:
            visit_date = parser.parse(history['LastVisitTime'])
        except:
            continue

        # stop parsing old history
        if (now - visit_date).total_seconds() > delta:
            break
        
        # filter urls
        visit_url = history['Url'] if 'Url' in history else history['URL']
        visit_title = history['Title']
        schema = visit_url.split('://')[0]
        # if schema in ['file', 'chrome', 'about', 'chrome-extension']:
        #     continue
        if not schema in ['http', 'https']:
            continue
        domain = visit_url.split('/')[2]
        domain = domain.split(':')[0]
        exclude = [item for item in exclude_domains if item in domain]
        if exclude:
            continue

        if sys.version_info[0] < 3:
            # Python 2.x, Only work on Unix compatible OSes
            try:
                tz = '/'.join(os.path.realpath('/etc/localtime').split('/')[-2:])
                tz = pytz.timezone(tz)
                local_time = visit_date.astimezone(tz).strftime("%Y/%m/%d %H:%M:%S")
            except:
                local_time = visit_date.strftime("%Y/%m/%d %H:%M:%S UTC")
        else:
            local_time = visit_date.astimezone().strftime("%Y/%m/%d %H:%M:%S")

        # print("%s | %s | %s\n%s" % (local_time, domain, visit_title, visit_url))

        results.append({
            'browser': browser,
            'profile': profile,
            'full_name': acc_info.get('full_name'),
            'email': acc_info.get('email'),
            'domain': domain,
            'url': visit_url,
            'title': visit_title,
            'time': local_time,
            'visit_time': history['LastVisitTime'],
            'visit_count': history['VisitCount']
        })


if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg == "dump":
        dump_mode = True
        if len(sys.argv) > 2:
            dump_mode = sys.argv[2].lower()
    else:
        try:
            if arg.endswith('d'):
                delta = int(arg[:-1]) * 86400
            elif arg.endswith('h'):
                delta = int(arg[:-1]) * 3600
            elif arg.endswith('m'):
                delta = int(arg[:-1]) * 60
            else:
                delta = int(arg)
        except:
            delta = 0
        if len(sys.argv) > 2:
            run_mode = sys.argv[2].lower()
if delta <= 0:
    print("Usage: python fetch.py 1d|6h|30m|3600")
    sys.exit(0)

if not dump_mode:
    print("Fetching last %d seconds of browser history." % delta)
    import pytz
    from dateutil import parser
    now = datetime.now(pytz.utc)

results = []
comments = []
profile_data = []
output_files = ['results']   # ['results', 'css', 'js', 'data.js', 'results.html']
result_has_multiple_user_profiles = False   # True if using hbd v0.4.3+

# run hbd to get all history
if not dry_run:
    subprocess.call([HBD, '-f', 'json'], stdout=FNULL, stderr=FNULL)

# parse main history json files
history_files = list_history_files('./results')
for history_file in history_files:
    prefix = os.path.basename(history_file).split('_history.json')[0]
    browser = prefix
    profile = 'default'
    index = 0
    if '_' in prefix:
        browser = prefix.split('_')[0]
        profile = prefix[len(browser)+1:]
        if profile != 'default':
            try:
                index = int(prefix.split('_')[-1])
                result_has_multiple_user_profiles = True
            except:
                continue
    
    if not dump_mode:
        if run_mode != 'all' and run_mode != 'main' and run_mode != browser:
            continue
    
    browser_name = browser.title()
    profile_name = profile.replace('_', ' ').title()
    profile_path = get_chrome_profile_path(index)
    if not profile_path:
        continue
    
    profile_name_ns = "".join(x for x in profile_name if x.isalnum() or x in "._-")
    output_dir = os.path.join('results', browser_name + profile_name_ns)
    if not dry_run:
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        copy_files(browser, profile_path, output_dir)
    
    acc_info = get_chrome_acc_info(profile_path)
    comment = add_profile_info(browser_name, profile_name, acc_info)
    comments.append(comment)
    if isinstance(dump_mode, bool) or dump_mode == 'full' or dump_mode == browser:
        print(comment)
    
    if dump_mode:
        if dump_mode in ['full', 'main', browser, profile, profile_name.lower(), profile_name_ns.lower()]:
            dump_profile(profile_path, browser_name + profile_name, comment=comment)
    else:
        parse_history_file(history_file, browser_name, profile_name, acc_info)

if dump_mode or run_mode in ['all', 'chrome']:
    # run hbd with custom chrome profile dir
    chrome_profiles_dir = list_chrome_profile()
    for profile_path in chrome_profiles_dir:
        browser = 'chrome'
        browser_name = browser.title()
        profile_name = os.path.basename(profile_path)
        # print(profile_name)
        if result_has_multiple_user_profiles:
            if profile_name == 'Default' or profile_name.startswith('Profile '):
                continue
        
        profile_name_ns = "".join(x for x in profile_name if x.isalnum() or x in "._-")
        output_dir = os.path.join('results', browser_name + profile_name_ns)
        # output_files.append(output_dir)
        
        acc_info = get_chrome_acc_info(profile_path)
        comment = add_profile_info(browser_name, profile_name, acc_info)
        if profile_name != 'Default':
            comments.append(comment)
            if isinstance(dump_mode, bool) or dump_mode == 'full' or dump_mode == browser:
                print(comment)
        
        # run hbd with profile_path as argument
        if not dry_run:
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)
            subprocess.call([HBD, '-b', 'chrome', '-p', profile_path, '-f', 'json', '--dir', output_dir], stdout=FNULL, stderr=FNULL)
            copy_files(browser, profile_path, output_dir)
        
        if dump_mode:
            if dump_mode in ['full', 'chrome', profile_name.lower(), profile_name_ns.lower()]:
                dump_profile(profile_path, browser_name + profile_name, comment=comment)
        else:
            # parse chrome history file
            history_file = os.path.join(os.getcwd(), output_dir, 'chrome_default_history.json')   # hbd v0.4.3+
            if not os.path.exists(history_file):
                history_file = os.path.join(os.getcwd(), output_dir, 'chrome_history.json')
            parse_history_file(history_file, browser_name, profile_name, acc_info)

if dump_mode or run_mode in ['all', 'incogniton']:
    # run hbd with incogniton profile dir
    incogniton_profiles_dir = list_incogniton_profile()
    for profile_path in incogniton_profiles_dir:
        browser = 'incogniton'
        browser_name = browser.title()
        profile_name = os.path.basename(os.path.dirname(profile_path))
        # print(profile_name)
        
        profile_name_ns = "".join(x for x in profile_name if x.isalnum() or x in "._-")
        output_dir = os.path.join('results', browser_name + profile_name_ns)
        # output_files.append(output_dir)
        
        acc_info = get_chromium_acc_info(profile_path)
        full_name = acc_info.get('full_name')
        full_name_ns = "".join(x for x in full_name if x.isalnum() or x in "._-")
        comment = add_profile_info(browser_name, profile_name, acc_info)
        comments.append(comment)
        if isinstance(dump_mode, bool) or dump_mode == 'full' or dump_mode == browser:
            print(comment)

        # run hbd with profile_path as argument
        if not dry_run:
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)
            subprocess.call([HBD, '-b', 'chromium', '-p', profile_path, '-f', 'json', '--dir', output_dir], stdout=FNULL, stderr=FNULL)
            copy_files('chromium', profile_path, output_dir)

        if dump_mode:
            if dump_mode in ['full', 'incogniton', profile_name.lower(), full_name.lower()]:
                dump_profile(profile_path, browser_name + full_name_ns + profile_name[0:8], comment=comment)
        else:
            # parse chromium history file
            history_file = os.path.join(os.getcwd(), output_dir, 'chromium_default_history.json')   # hbd v0.4.3+
            if not os.path.exists(history_file):
                history_file = os.path.join(os.getcwd(), output_dir, 'chromium_history.json')
            parse_history_file(history_file, browser_name, profile_name, acc_info)

if dump_mode:
    if dump_mode == True or dump_mode in ['full', 'chrome']:
        dump_results(comment="\n".join(comments))
    sys.exit(0)

# sort results by visit time
results.sort(key=lambda x: x['visit_time'])

# write js
js_name = os.path.join(BASEDIR, 'data.js')
with open(js_name, mode='w') as f:
    f.write("var delta=%d,data=" % delta);
    json.dump(results, f)
    f.write(",profiles=");
    json.dump(profile_data, f)

print("Total %d histories found." % len(results))
# print(results_by_domain)

# open result page
HOMEPAGE = os.path.join(BASEDIR, 'results.html')
if sys.platform == 'darwin':
    subprocess.call(['open', HOMEPAGE], stdout=FNULL, stderr=FNULL)
if sys.platform == 'linux':
    subprocess.call(['google-chrome', HOMEPAGE], stdout=FNULL, stderr=FNULL)
elif sys.platform == 'win32':
    subprocess.call(['cmd', '/c', 'start', HOMEPAGE], stdout=FNULL, stderr=FNULL)
