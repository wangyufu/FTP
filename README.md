FTP   
==
作者:王宇夫     

## 程序介绍:		 
    使用python3+,Windows环境使用；    
	多用户登录进行上传下载，可以加md5校验文件。      

## 优化项    
	上传下载进度条；    
	上传时判断家目录存储配额；    
	cd切换目录，锁定到自己的家目录；     
	pwd查看当前路径、del功能；     
	del删除文件。    
	
## 程序使用：   
	1、打开FTPServer\bin目录，执行python ftp_server.py          
	2、打开FTPClient目录，执行python ftp_client.py -s 127.0.0.1 -P 2121    
	3、在client端登录server端已有的账户，wang\123456 | test\123456    
	3、在client输入命令    
		下载家目录的文件：    
		get <家目录已有的文件>    
		get <家目录已有的文件>  --md5    
		
		上传文件到家目录：    
		put <绝对路径文件>    
		put <绝对路径文件>  --md5   

		查看家目录文件：       
		ls     
		
		查看当前ftp路径：      
		pwd     
		
		切换ftp目录：   
		cd <相对路径>     
		
		删除文件：    
		del <相对路径文件>     
		
		帮助：    
		help     

		退出：    
		exit     
