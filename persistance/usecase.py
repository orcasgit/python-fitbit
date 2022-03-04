from fitbit.api import Fitbit
from oauth2.server import OAuth2Server
from persistance.firestore import FirestoreImpl

class StoreUsecase():
    def __init__(self, fitbit: Fitbit, firestore: FirestoreImpl, start_date, end_date):
        self.fitbit = fitbit
        self.firestore = firestore
        self.start_date = start_date
        self.end_date = end_date

    def get_profile(self):
        profile = self.fitbit.user_profile_get()['user']
        print("\n--------------------------------------------------")
        print('You are authorized to access data for the user: {}'.format(profile['fullName']))
        print("--------------------------------------------------\n")
        self.firestore.store_profile(profile)
        return profile['encodedId']

    def get_intraday(self):
        steps = self.fitbit.intraday_time_series(
            resource="steps", 
            start_date=self.start_date,
            end_date=self.end_date)
        self.firestore.store_intraday(data=steps, doc_name="steps")

        calories = self.fitbit.intraday_time_series(
            resource="calories", 
            start_date=self.start_date,
            end_date=self.end_date)
        self.firestore.store_intraday(data=calories, doc_name="calories")
        
        distance = self.fitbit.intraday_time_series(
            resource="distance", 
            start_date=self.start_date,
            end_date=self.end_date)
        self.firestore.store_intraday(data=distance, doc_name="distance")

        heart = self.fitbit.intraday_time_series(
            resource="heart", 
            start_date=self.start_date,
            end_date=self.end_date)
        self.firestore.store_intraday(data=heart, doc_name="heart")

        # does not work!
        # elevation = self.fitbit.intraday_time_series(
        #     resource="elevation", 
        #     start_date=self.start_date,
        #     end_date=self.end_date)

        # does not work!
        # floor = self.fitbit.intraday_time_series(
        #     resource="floors", 
        #     start_date=self.start_date,
        #     end_date=self.end_date)

    def get_resources(self):
        return
    
    def get_time_series(self):
        sleeps = self.fitbit.time_series(
            resource='sleep', 
            api_version=1.2,
            base_date=self.start_date,
            end_date=self.end_date)
        self.firestore.store_time_series(data=sleeps, doc_name="sleeps")

