import conf, json, time, math, statistics
from boltiot import Sms, Bolt, Email

#computing the threshold using "Z-Score analysis"
def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound]


#sensor value=temperature*10.24
minimum_temp_limit = 4*10.24 
maximum_temp_limit = 20*10.24

#api authentication
mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
sms = Sms(conf.SSID, conf.AUTH_TOKEN, conf.TO_NUMBER, conf.FROM_NUMBER)
mailer = Email(conf.MAILGUN_API_KEY, conf.SANDBOX_URL, conf.SENDER_EMAIL, conf.RECIPIENT_EMAIL)

history_data=[]
while True:
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    
    print("Sensor value : "+data['value'])
    temperature=float(data['value'])/10.24
    print("Temperature : "+str(temperature))
    sensor_value=0
    try:
        sensor_value = int(data['value'])
    except Exception as e:
        print("There was an error while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
    if not bound:
        required_data_count=conf.FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        if sensor_value > bound[0] :
            print ("The temperature level increased suddenly. Sending an SMS and Email Alert.")
            response = sms.send_sms("The refrigerator has been opened")
            print("This is the response from Twilio ",response)

            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The Current temperature sensor value is " +str(sensor_value)+ " and temperature is " + str(
            temperature) + " degree Celsius.")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        elif sensor_value < bound[1]:
            print ("The temperature level decreased suddenly. Sending an SMS and Email Alert.")
            response = sms.send_sms("The refrigerator has been closed")
            print("This is the response from Twilio ",response)

            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The Current temperature sensor value is " +str(sensor_value)+ " and temperature is " + str(
            temperature) + " degree Celsius.")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        elif sensor_value>maximum_temp_limit:
            print ("The temperature level crossed the maximum limit. Sending an SMS and Email Alert.")
            response = sms.send_sms("The temperature level crossed the maximum limit")
            print("This is the response from Twilio ",response)

            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The Current temperature sensor value is " +str(sensor_value)+ " and temperature is " + str(
            temperature) + " degree Celsius.")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        elif sensor_value<minimum_temp_limit:
            print ("The temperature level went below the minimum limit. Sending an SMS and Email Alert.")
            response = sms.send_sms("The temperature level went below the minimum limit")
            print("This is the response from Twilio ",response)

            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The Current temperature sensor value is " +str(sensor_value)+ " and temperature is " + str(
            temperature) + " degree Celsius.")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        history_data.append(sensor_value)
    except Exception as e:
        print ("Error",e)
    time.sleep(10)
