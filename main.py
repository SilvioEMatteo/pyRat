import sys
import cv2
import datetime
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.uic import loadUi


class BetaSensoreMovimento(QDialog):
    def __init__(self):
        super(BetaSensoreMovimento, self).__init__()
        loadUi('interfacciaBeta.ui', self)


        self.liveFrame = None
        self.bottoneAvviaWebcam.toggled.connect(self.avviaWebcam)
        self.bottoneAvviaWebcam.setCheckable(True)
        self.bottoneStopWebcam.toggled.connect(self.stopWebcam)
        self.bottoneStopWebcam.setCheckable(True)
        self.bottoneStopWebcam.setEnabled(False)
        self.flagMotion=None
        self.bottonePrimoFrame.clicked.connect(self.primoFrameMotion)
        self.bottoneCatturaMovimento.toggled.connect(self.statusBottoneCatturaMovimento)
        self.bottoneCatturaMovimento.setCheckable(True)
        self.bottoneCatturaMovimentoAttivo= False
        self.motionFrame=None
        self.tempoCompletoDiDataEOra = ''
        self.tempoInizio=None
        self.tempoFine=None
        self.tempoDurata=None
        self.esitoMovimento=False
        self.flagInizio=False
        self.cont=True

    def statusBottoneCatturaMovimento(self,status):
        if status:
            self.bottoneCatturaMovimentoAttivo=True
            self.bottoneCatturaMovimento.setText('Fine Cattura')
        else:
            self.bottoneCatturaMovimentoAttivo=False
            self.bottoneCatturaMovimento.setText('Cattura Movimento')

    def detectMotion(self,input_img):
        self.text='Nessun Movimento'
        self.flagMotion=False
        gray= cv2.cvtColor(input_img,cv2.COLOR_BGR2GRAY)
        gray=cv2.GaussianBlur(gray,(21,21),0)

        frameDiff= cv2.absdiff(self.motionFrame,gray)
        thresh=cv2.threshold(frameDiff,5,255,cv2.THRESH_BINARY)[1]

        thresh=cv2.dilate(thresh,None,iterations=5)

        im2,cnts,hierarchy= cv2.findContours(thresh.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        try:
            hierarchy=hierarchy[0]
        except:
            hierarchy=[]

        height, width, channels=input_img.shape
        min_x,min_y=width,height
        max_x= max_y= 0

        for contour,hier in zip(cnts,hierarchy):
            (x,y,w,h)=cv2.boundingRect(contour)
            min_x,max_x= min(x,min_x),max(x+w,max_x)
            min_y,max_y= min(y,min_y),max(y+h,max_y)

        if max_x-min_x>80 and max_y-min_y>80:
            cv2.rectangle(input_img,(min_x,min_y),(max_x,max_y),(0,255,0),3)
            self.text='Movimento Rilevato'
            self.flagMotion=True

        cv2.putText(input_img,'Stato Movimento: {}'.format(self.text),(10,20),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
        cv2.putText(input_img, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, input_img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return input_img,self.flagMotion

    def primoFrameMotion(self):
        grigio=cv2.cvtColor(self.liveFrame.copy(),cv2.COLOR_BGR2GRAY)
        grigio=cv2.GaussianBlur(grigio,(21,21), 0)
        self.motionFrame=grigio
        self.visualizzaFrame(grigio,2)

    def stopWebcam(self):
        self.bottoneStopWebcam.setEnabled(False)
        self.bottoneAvviaWebcam.setEnabled(True)
        self.timer.stop()
        self.labelLiveCam.clear()
        self.labelPrimoFrame.clear()

    def avviaWebcam(self):
        self.bottoneAvviaWebcam.setEnabled(False)
        self.bottoneStopWebcam.setEnabled(True)
        self.cattura= cv2.VideoCapture(1)
        self.cattura.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cattura.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.timer= QTimer(self)
        self.timer.timeout.connect(self.aggiornaFrame)
        self.timer.start(30)
        #Successivamente creazione parametro regolabile da utente in base alla telecamera (FRAME RATE)


    def aggiornaFrame(self):
        ritorno,self.liveFrame = self.cattura.read()
        self.liveFrame = cv2.flip(self.liveFrame,1)

        if self.bottoneCatturaMovimentoAttivo:
            movimentoCatturato,self.esitoMovimento=self.detectMotion(self.liveFrame.copy())
            self.visualizzaFrame(movimentoCatturato,1)
            if self.esitoMovimento:
                if self.cont:
                    self.tempoInizio=time.time()
                    self.flagInizio=True
                    self.tempoCompletoDiDataEOra = ''
                    self.prendiTempoInizioMotion()
                    self.lineaInizioMovimento.setText(self.tempoCompletoDiDataEOra)
                    self.cont=False
            else:
                if self.flagInizio:
                    self.tempoFine = time.time()
                    self.tempoCompletoDiDataEOra = ''
                    self.prendiTempoInizioMotion()
                    self.lineaFineMovimento.setText(self.tempoCompletoDiDataEOra)
                    self.tempoDurata = self.tempoFine - self.tempoInizio
                    self.lineaDurataMovimento.setText(str(self.tempoDurata))
                    self.flagInizio=False
                    self.cont=True

        else:

            self.visualizzaFrame(self.liveFrame,1)

        self.primoFrameMotion()


    def prendiTempoInizioMotion(self):
        oggettoTempo=datetime.datetime.now()
        app=str(oggettoTempo)
        for i in range(11,19):
            self.tempoCompletoDiDataEOra=self.tempoCompletoDiDataEOra+app[i]

    def visualizzaFrame(self,frame,window=1):
        qformat = QImage.Format_Indexed8
        if len(frame.shape)==3: # [0]=righe [1]=colonne [2]=canali
            if frame.shape[2]==4:
                qformat=QImage.Format_RGBA8888
            else:
                qformat=QImage.Format_RGB888
        outputFrame=QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], qformat)
        #Conversione da BGR a RGB
        outputFrame=outputFrame.rgbSwapped()
        if window == 1:
            self.labelLiveCam.setPixmap(QPixmap.fromImage(outputFrame))
            self.labelLiveCam.setScaledContents(True)
        if window == 2:
            self.labelPrimoFrame.setPixmap(QPixmap.fromImage(outputFrame))
            self.labelPrimoFrame.setScaledContents(True)




if __name__=='__main__':
    applicazione=QApplication(sys.argv)
    finestraBeta= BetaSensoreMovimento()
    finestraBeta.setWindowTitle('Beta pyRat')
    finestraBeta.show()
    sys.exit(applicazione.exec_())







