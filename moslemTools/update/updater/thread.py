import os ,shutil ,subprocess ,requests ,settings ,guiTools ,time 
import PyQt6 .QtWidgets as qt 
import PyQt6 .QtGui as qt1 
import PyQt6 .QtCore as qt2 




class DownloadUpdateThread (qt2 .QThread ):
    progress =qt2 .pyqtSignal (int )
    installing =qt2 .pyqtSignal (str )
    finish =qt2 .pyqtSignal (str )
    network_error =qt2 .pyqtSignal (str )

    def __init__ (self ,URL ,parent=None ):
        super ().__init__ (parent )
        self .URL =URL 
        self .path =os .path .join (os .getenv ('appdata'),settings .settings_handler .appName ,"update")
        self .is_paused =False 
        self .is_cancelled =False 

    def pause (self ):
        self .is_paused =True 

    def resume (self ):
        self .is_paused =False 

    def cancel (self ):
        self .is_cancelled =True 

    def run (self ):
        os .makedirs (self .path ,exist_ok =True )
        Name =os .path .join (self .path ,self .URL .split ("/")[-1 ])
        while not self .is_cancelled :
            if self .is_paused :
                self .msleep (200 )
                continue 
            downloaded_size =os .path .getsize (Name )if os .path .exists (Name )else 0 
            headers ={
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            }
            if downloaded_size >0 :
                headers ['Range']=f'bytes={downloaded_size}-'
            try :
                r =requests .get (self .URL ,stream =True ,timeout =15 ,headers =headers )
                if r .status_code in (200 ,206 ):
                    content_range =r .headers .get ('content-range')
                    if content_range :
                        total_size =int (content_range .split ('/')[-1 ])
                    elif 'content-length'in r .headers :
                        total_size =downloaded_size +int (r .headers ['content-length'])
                    else :
                        total_size =0 
                    mode ="ab"if (downloaded_size >0 and r .status_code ==206 )else "wb"
                    if mode =="wb":
                        downloaded_size =0 
                    with open (Name ,mode )as file :
                        for chunk in r .iter_content (chunk_size =1024 ):
                            while self .is_paused and not self .is_cancelled :
                                self .msleep (200 )
                            if self .is_cancelled :
                                self .finish .emit ("cancelled")
                                return 
                            if chunk :
                                file .write (chunk )
                                downloaded_size +=len (chunk )
                                if total_size >0 :
                                    self .progress .emit (int ((downloaded_size /total_size )*100 ))
                                else :
                                    self .progress .emit (int (downloaded_size /1024 )%100 )
                    self .installing .emit ("yes")
                    self .finish .emit (Name )
                    return 
                else :
                    self .finish .emit ("error")
                    return 
            except (requests .exceptions .RequestException ,Exception ):
                self .is_paused =True 
                self .network_error .emit ("تم انقطاع الاتصال بالإنترنت وتم إيقاف التحميل مؤقتاً. يرجى التأكد من الاتصال ثم الضغط على زر الاستئناف.")


