from pprint import pprint

def user_input_confirm(msg, prefix=''):
    """Ask the user if he confirm the msg question.

    :rtype: True if user confirm, False if not"""
    answer = raw_input(msg)
    if answer == 'n':
        return False
    return True


def user_input_choose_amongst(choices, prefix=''):
    """Ask the user if he confirm the msg question.

    :rtype: True if user confirm, False if not"""
    while True:
        print "%sYou must choose a provide amongst:" % prefix
        for i, c in enumerate(choices) :
            print "  %s%d) %s" % (prefix, i, c)
        answer = raw_input("%sChoose a provide [0-%d]: " % (prefix, len(choices)-1))
        try:
            return choices[int(answer)]
        except Exception as e:
            print e
            print "%sInvalid choice. Do it again!" % (prefix)


def user_input_choose_amongst(choices, prefix=''):
    """Ask the user if he confirm the msg question.

    :rtype: True if user confirm, False if not"""
    while True:
        print "%sYou must choose a provide amongst:" % prefix
        for i, c in enumerate(choices) :
            print "  %s%d) %s" % (prefix, i, c)
        answer = raw_input("%sChoose a provide [0-%d]: " % (prefix, len(choices)-1))
        try:
            return choices[int(answer)]
        except Exception as e:
            print e
            print "%sInvalid choice. Do it again!" % (prefix)
         

import logging
logging.basicConfig(level=logging.INFO)

import argparse
parser = argparse.ArgumentParser(prog='mss3-iter-smart')
parser.add_argument(dest="xpath", type=str, help='A provide Xpath')
args = parser.parse_args()

import mss.transports
lfm = mss.transports.Transport(modules_dir="mss/modules/",os_type=mss.utils.OsType("Mandriva Business Server"))

from mss.client.iter_smart import Provide, walk

root_provide = Provide(generic_xpath=args.xpath, lfm=lfm)

generator = walk(root_provide)
while True:
    try:
        (provide, step, args) = generator.next()
    except StopIteration:
        break

    print "%s [%s] " % (provide.generic_xpath.ljust(60+2*provide.depth), provide.step)
    if provide.step == "manage":
        ret = user_input_confirm("Manage %s [Y/n]? " % provide.generic_xpath)
        provide.manage(ret)

    elif provide.step == "specialize":
        matches = provide.matches()
        if len(matches) > 1:
            ret = user_input_choose_amongst(matches, "")
            provide.specialize(ret)
        else:
            provide.specialize(matches[0])
            
    elif provide.step == "multiplicity":
        require = args
        while True:
            answer = raw_input("How many time to call %s? " % require.provide_xpath)
            try:
                answer = int(answer)
                break
            except Exception as e:
                print e
                print "Invalid choice. Do it again!"
        generator.send(answer)
            
    elif provide.step == "done":
        ret = user_input_confirm("Call %s [Y/n]?" % provide.generic_xpath)
        if ret:
            print "Configuration requires of %s" %provide.generic_xpath
        
        

