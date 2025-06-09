from notifypy import Notify
from settings import  app
def SendNotification(title,message):
	notification = Notify()
	notification.title = title
	notification.message = message
	notification._notification_application_name=app.name
	notification.send()