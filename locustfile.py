from my_settings import Token
from locust import HttpUser, task, between


# class WebsiteTestUser(HttpUser):
#     wait_time = between(1, 2.5)

#     @task
#     def my_task(self):
#         self.token   = Token
#         self.headers = {'Authorization' : self.token}
#         self.client.get('/product/info?offset=0&limit=10', headers= self.headers)

class SheetInbound(HttpUser):
    wait_time = between(1, 2.5)

    @task
    def task_inbound(self):
        self.token   = Token
        self.headers = {'Authorization' : self.token}
        self.data = {
            "type" : "inbound",
            "date" : "2023-01-09",
            "company_id": 2,
            "etc"  : "cLocust - test1",
            "products" : [
                {
                    "product_code": "EXPP001",
                    "quantity"  : 10,
                    "location"  : "위치",
                    "price"     : 30000,
                    "warehouse_code" : "A",
                    "etc"       : "Locust - test1"
                },
                {
                    "product_code": "SWVV001",
                    "quantity"  : 10,
                    "location"  : "위치",
                    "price"     : 13000,
                    "warehouse_code" : "A",
                    "etc"       : "Locust - test1"
                },
                {
                    "product_code": "BT001",
                    "quantity"  : 20,
                    "location"  : "위치",
                    "price"     : 200,
                    "warehouse_code" : "A",
                    "etc"       : "Locust - test1"
                }
                ]}
        self.client.post('/stock/sheet', headers= self.headers, json= self.data)


# class ProductList(HttpUser):
#     wait_time = between(1, 2.5)

#     @task
#     def task_list(self):
#         self.token   = Token
#         self.headers = {'Authorization' : self.token}
        # self.client.get('/product/info?offset=0&limit=10', headers= self.headers)