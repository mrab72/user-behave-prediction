# user behavior prediction

Nowadays, by increasing the number of users and the bandwidth's limitations, Internet Service providers need automatic resource allocations.
For this purpose, they should be familiar with their users and their usage.
 
 For example, if they know when a specific user is watching youtube, they can allocate more bandwidth than when they just read a web page.
So by knowing the user behavior in the network during the time, we can allocate bandwidth properly.

On the other hand, by knowing and monitoring traffic's general usage, The ISPs can be alert the attacks before they happened.also, they can the health of their systems by real traffics base on user usage.
In this project, we try to predict user behavior in the internet network. 

Our purpose of user behavior is the type of traffic used. The types include:
[Web, Email, Chat, Social Media, Network, SoftwareUpdate, VPN, System, RemoteAccess, File-Transfering-Download,...]

We use sequence modeling methods; specifically, we use machine learning methods, such as classifiers and deep learning algorithms, because they have great potential for predicting time sequences.
As a case study, we use the data of 100 static IP.


 We collected the data for five months; then, we discuss how to solve the prediction problems and suggest a classifier method.

At first, we try to capture the users' data by the following steps.
## Data Collection
1) capture data by using the TCPDUMP package
2) remove PPOEEE headers
3) remove arp and dns packets by using the TCPDUMP package
4) extract flows by using the TCPDUMP package
5) pull traffic type by DPI (Deep Packet Inspection)

Then we require to save extracted data in the DB.

The input rate of our channel is 1GB/s. Therefore the bottleneck is the time for each mentioned step and the memory resource; for example, the required memory to process the 5 minutes captured data is about 10GB. The required time is about 30 minutes, so we can't handle this big data.

Therefore we pipelined the preprocess steps, so we use the Celery package to have a series of tasks.


At the end of data collections, we have records of data in MongoDB.

```
{
'bandwidth': 0.0005383854968491407,
 'date': '2020-02-21',
 'destination_ip': '84.241.0.93',
 'first_timestamp': 1582250124.044764,
 'hour': '01:55:24.044764',
 'id': ObjectId('5e4f44b17e200f2ec2e68deb'),
 'last_timestamp': 1582250332.074142,
 'source_ip': '',
 'traffic_type': 'Web'
}
```
Inn every app directory, I add required readme to.
## Data Engineering

## Training Model
