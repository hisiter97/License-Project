import rsa
from base64 import b64encode, b64decode

import os
from datetime import date, timedelta, datetime
from urllib.request import urlopen, URLError
from database import LicenseDatabase
import random

PUBLIC_KEY_PATH = "./key_dir/public.key"                    # save to client application
PRIVATE_KEY_PATH = "./key_dir/private.key"                  # only save on sever

PAGE_GET_TIME = 'http://just-the-time.appspot.com/'
# LICENSE =  KEYGEN + DATA_EXPIRED (KEYGEN == rsa)

class LICENSE_SEVER:

    def __init__(self, create_new=False):

        if create_new:
            self.public_key, self.private_key = rsa.newkeys(512)   # same for all user, sent public_key with application
            with open(PUBLIC_KEY_PATH, 'wb') as p_file:
                p_file.write(self.public_key.save_pkcs1(format='PEM'))
            with open(PRIVATE_KEY_PATH, 'wb') as pri_file:
                pri_file.write(self.private_key.save_pkcs1(format='PEM'))
        else:
            if os.path.exists(PUBLIC_KEY_PATH):
                with open(PUBLIC_KEY_PATH, 'rb') as pub_file:
                    public_key = b''.join(pub_file.readlines())
                    self.public_key = rsa.PublicKey.load_pkcs1(keyfile=public_key, format='PEM')
            if os.path.exists(PRIVATE_KEY_PATH):
                with open(PRIVATE_KEY_PATH, 'rb') as pri_file:
                    private_key = b''.join(pri_file.readlines())
                    self.private_key = rsa.PrivateKey.load_pkcs1(keyfile=private_key, format='PEM')
        self.db = LicenseDatabase()

    def genLicense(self, data, duration_license=30):
        """

        :param data: a dict: {'email': ..., 'MAC': ... }
        :return: key
        """

        # DATE EXPIRED
        if self.check_have_internet():
            date_today = self.get_time_online()
        else:
            print("Not internet !")
            date_today = date.today()
        date_expired = date_today + timedelta(days=duration_license)
        date_expired = date_expired.strftime('%Y%m%d')          # str
        date_expired_byte = date_expired.encode('ascii')
        date_expired_encoded = b64encode(date_expired_byte)

        #KEYGEN
        data_str = "".join(data.values())
        keygen = rsa.sign(data_str.encode('utf-8'), priv_key=self.private_key, hash_method='SHA-1')
        keygen = b64encode(keygen).decode('ascii')      # byte -> str

        # LICENSE = DATE_EXPIRED + KEYGEN
        self.length_date_encode = len(date_expired_encoded.decode('utf-8'))
        date_expired_str = date_expired_encoded.decode('utf-8')

        license = self.create_license_from_key_and_date(keygen, date_expired_str)
        print("Date expired: ", datetime.strptime(date_expired, '%Y%m%d').date())


        ## Add to database
        is_found = self.db.findLicense(license)
        if is_found:
            print("Error: Exists this license")
            return None
        else:
            #print("Added license to db")
            self.db.addLicense(license)

        return license



    def checkLicense(self, license):
        """
        Kiem tra license: Neu chua kich hoat thi kich hoat va return False
        :param license:
        :return:
        """
        is_found = self.db.findLicense(license)
        if is_found:
            return self.activeLicense(license)

    def activeLicense(self, license):
        return self.db.updateNumActivedLicense(license)

    def getPublicKey(self):
        return self.public_key

    def getPrivateKey(self):
        return self.private_key


    def get_key_and_date_from_license(self, license):
        """

        :param license:
        :return: keygen and data_expired
        """
        keygen, date_expired = license[:-11], license[-11:]
        keygen = keygen + "=="
        date_expired = date_expired + "="
        return keygen, date_expired

    def create_license_from_key_and_date(self, key_str, date_str):
        license = key_str[:-2] + date_str[:-1]   # remove '=' character
        return license

    def get_time_online(self):
        """

        :return: date object
        """
        page_time = urlopen(PAGE_GET_TIME)
        time_now = page_time.read().strip()
        date_now = datetime.strptime(time_now.decode('utf-8'), '%Y-%m-%d %H:%M:%S').date()
        return date_now

    def check_have_internet(self):
        try:
            urlopen('http://216.58.192.142', timeout=1)
            return True
        except URLError as err:
            return False

    # def checkLicense_v1 (self, data, license):
    #     """
    #
    #     :param data: a dict: {'email': ..., 'MAC': ... }
    #     :param keygen:
    #     :return: is valid ?
    #     """
    #
    #     data_str = "".join(data.values())
    #     keygen, data_expired = self.get_infor_from_license(license)         # str type
    #
    #     try:
    #         keygen = b64decode(keygen.encode('ascii'))
    #         rsa.verify(data_str.encode('utf-8'), signature=keygen, pub_key=self.public_key)
    #     except rsa.VerificationError:
    #         print("Invalid key")
    #         return False
    #     else:
    #         print("Valid key")
    #         return True



if __name__ == "__main__":

    ### At sever
    ## Step 1: Sever generate private and public key (only once)
    lis = LICENSE_SEVER(create_new=False)

    data = {"email": "hoanglv@mail"}
    license = lis.genLicense(data=data)
    print(license)

