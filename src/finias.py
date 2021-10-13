import os
import requests
from msal import ConfidentialClientApplication
import json
from tabulate import tabulate
from slackhandler import slackHandler

"""Python\Flask app to interface with Azure API
   primarily to play around with billing/subscriptions/roles API
   if ran with daemon option it'll act as Slack Bot/eventhandler
   Bas van Veen <bas@dopdop.nl>
"""

class Insights:

    def __init__(self, options, args):
        self.options = options
        self.args = args
        # Azure endpoint todo MSAL auth
        self.azureURI = "https://management.azure.com/"
        # Do MSAL , replaced adal(old method auth)
        self.headers, self.params = AzureConnection.getInstance().getAuthorizationHeaderWithParams()
        # Default to first subscription ID
        self.subscription = self.getSubscriptionID()
        #if options.daemon:
        self.slackhandler = slackHandler(self)

    def listSubscriptions(self):
        r = requests.get(self.azureURI + 'subscriptions', headers=self.headers, params=self.params)
        data = []
        for subscription in r.json()['value']:
            data.append([subscription['displayName'],subscription['id'],subscription['authorizationSource']])
        print(tabulate(data, headers=['displayName', 'id', 'authorizationSource']))

    def getSubscriptions(self):
        r = requests.get(self.azureURI + 'subscriptions', headers=self.headers, params=self.params)
        data = []
        for subscription in r.json()['value']:
            data.append([subscription['displayName'],subscription['id'],subscription['authorizationSource']])
        return tabulate(data, headers=['displayName', 'id', 'authorizationSource'])

    def getSubscriptionID(self):
        r = requests.get(self.azureURI + 'subscriptions', headers=self.headers, params=self.params)
        data = []
        for subscription in r.json()['value']:
            return subscription['id']

    def listRoleAssignments(self):
        params = {'api-version': '2021-04-01-preview'}
        r = requests.get(self.azureURI + self.subscription + '/providers/Microsoft.Authorization/roleAssignments', headers=self.headers, params=params)
        data = []
        print(r.json())
        for assignment in r.json()['value']:
            data.append([assignment['name'],assignment['properties']['principalType'],assignment['properties']['scope'],assignment['properties']['createdOn']])
        print(tabulate(data, headers=['name','principalType','scope','createdOn']))

    def getRoleAssignments(self):
        params = {'api-version': '2021-04-01-preview'}
        r = requests.get(self.azureURI + self.subscription + '/providers/Microsoft.Authorization/roleAssignments', headers=self.headers, params=params)
        data = []
        print(r.json())
        for assignment in r.json()['value']:
            data.append([assignment['name'],assignment['properties']['principalType'],assignment['properties']['scope'],assignment['properties']['createdOn']])
        return tabulate(data, headers=['name','principalType','scope','createdOn'])


        
class AzureConnection:

    __shared_instance = 'singleton'
    token = ''
    params = {'api-version': '2021-04-01'}
 
    @staticmethod
    def getInstance():
 
        """Static Access Method"""
        if AzureConnection.__shared_instance == 'singleton':
            AzureConnection()
        return AzureConnection.__shared_instance
 
    def __init__(self):
 
        """virtual private constructor"""
        if AzureConnection.__shared_instance != 'singleton':
            raise Exception ("singleton class can't redefine")
        else:
            # Instantiate one self
            self.connect()            
            AzureConnection.__shared_instance = self

    def connect(self):
        tenant = os.environ['TENANT']
        authority_url = 'https://login.microsoftonline.com/' + tenant
        client_id = os.environ['CLIENTID']
        client_secret = os.environ['CLIENTSECRET']
        resource = 'https://management.azure.com/'
        app = ConfidentialClientApplication(client_id, authority=authority_url, client_credential=client_secret)
        self.token = app.acquire_token_for_client('https://management.azure.com//.default')
    
    def getAuthorizationHeaderWithParams(self):
        params = self.params
        return  {'Authorization': 'Bearer ' + self.token['access_token'], 'Content-Type': 'application/json'}, self.params
