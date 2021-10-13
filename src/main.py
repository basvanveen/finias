from optparse import OptionParser
from finias import Insights

"""Python\Flask app to interface with Azure API
   primarily to play around with billing/subscriptions/roles API
   if ran with daemon option it'll act as Slack Bot/eventhandler
   Bas van Veen <bas@dopdop.nl>
"""

parser = OptionParser()
parser.add_option("-d", "--daemon", dest="daemon",
                  help="Run Finias as a daemon/bot", metavar="DAEMON")
parser.add_option("-p", "--provider",
                  action="store_false", dest="provider", default="azure",
                  help="Specify cloud provider, default is Azure")


(options, args) = parser.parse_args()


def main():
    f = Insights(options, args)
    #f.listSubscriptions()
    #f.listRoleAssignments()


if __name__ == "__main__":
    main()
