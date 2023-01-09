from my_settings import Token
from locust import HttpUser, task, between


class WebsiteTestUser(HttpUser):
    wait_time = between(1, 2.5)

    @task
    def my_task(self):
        self.token   = Token
        self.headers = {'Authorization' : self.token}
        self.client.get('/product/info?offset=0&limit=10', headers= self.headers)