import requests
from requests.auth import HTTPBasicAuth
import click

from githubstats.repo import Repo
from githubstats.user import User

def run_query(self, query):
        URL = 'https://api.github.com/graphql'

        headers = {"Authorization": "Bearer 727f4c8843e3e8c1ecf485dbe4429dfdca3fcffe"}

        request = requests.post(URL, json=query,headers=headers)

        #print(self.github.user_pass)
        #print(self.github.user_login)

        #request = requests.post(URL, json=query,auth=HTTPBasicAuth("gleisonbt", "Aleister93"))

        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def user_type(self, item_id):
        queryType="""
                    query type($queryUser:String!){
                        search(query:$queryUser, type:USER, first:100){
                            nodes{
                                ... on Actor{
                                __typename
                            }
                        }
                    }
                    }
                    """
        jsonType = {
            "query": queryType, "variables":{
            "queryUser": "user:" + item_id
            }
        }

        result = self.run_query(jsonType)
        
        return result["data"]["search"]["nodes"][0]["__typename"]

def user_data(self, item_id, ):

        item_type = self.user_type(item_id)

        prefixQueryUser = """
            query findUser($user:String!){
                user(login:$user){
        """

        prefixQueryOrganization = """
            query findOrganization($user:String!){
            organization(login:$user){
        """

        prefix = None
        if item_type == "User":
            prefix = prefixQueryUser
        else:
            prefix = prefixQueryOrganization

        query =  prefix + """
                    name
                    location
                }
                }    
        """

        json = {
            "query":query, "variables":{
                "user":item_id
            }
        }

        result = self.run_query(json)
        
        #print(result)

        if item_type == "User":
            return {"name":result["data"]["user"]["name"],
            "location":result["data"]["user"]["location"], "type":item_type}
        else:
            return {"name":result["data"]["organization"]["name"],
            "location":result["data"]["organization"]["location"], "type":item_type}

def print_rate_limit(self):
        """Prints the rate limit."""

        query = """
            query { 
                rateLimit{
                    remaining
                }
            }
        """

        json = {
            "query":query, "variables":{}
        }

        result = run_query(self,json)["data"]["rateLimit"]["remaining"]

        click.echo('Rate limit: ' + str(result))

def search_repositories(self, query, sort='stars'):
        queryRepos = """
            query findRepos($query:String!){
            search(query:$query, type:REPOSITORY, first:100{AFTER}){
                pageInfo{
                hasNextPage
                endCursor
                }
                nodes{
                ... on Repository{
                    nameWithOwner
                    stargazers{
                    totalCount
                    }
                    forks{
                    totalCount
                    }
                    description
                    primaryLanguage{
                    name
                    }
                }
                }
            }
            rateLimit{
                remaining
                resetAt
            }
            }    
        """

        fistQuery = queryRepos.replace("{AFTER}", "")

        json = {
            "query":fistQuery, "variables":{
                "query":query + " sort:" + sort
            }
        }

        result = run_query(self,json)

        nodes = result["data"]["search"]["nodes"]

        next_page  = result["data"]["search"]["pageInfo"]["hasNextPage"]
        while next_page:
            cursor = result["data"]["search"]["pageInfo"]["endCursor"]
            next_query = queryRepos.replace("{AFTER}", ", after: \"%s\"" % cursor)
            json["query"] = next_query
            result = run_query(self,json)
            nodes += result["data"]["search"]["nodes"]
            next_page  = result["data"]["search"]["pageInfo"]["hasNextPage"]
        
        repositories = []
        for node in nodes:
            repositories.append(Repo(node["nameWithOwner"], node["stargazers"]["totalCount"],
                    node["forks"]["totalCount"], node["description"], node["primaryLanguage"]["name"]))


        return repositories
