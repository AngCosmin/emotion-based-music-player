# emotion-detection

## Start
1. Duplicate `.env.example` and rename one of them to `.env`

### Get imgur key
1. Create an account on imgur  
2. Go [HERE](https://imgur.com/account/settings/apps) and create an app  
3. Paste `client id` and `client secret` in `.env`  
  
### Get Microsoft Cognitive Services key
1. Go [HERE](https://azure.microsoft.com/en-us/services/cognitive-services/face/)  
2. Press `Try free` and get 7 days trial  
3. Login  
4. Go [HERE](https://azure.microsoft.com/en-us/try/cognitive-services/my-apis/)
5. Copy one of these keys in `.env`

### Install packages
`pip install -r requirements.txt --user`

### If you want to edit UI
You can install QtDesigner from [HERE](https://build-system.fman.io/qt-designer-download)

#### On Mac
Run `brew install ffmpeg`