### 1. 环境

Python版本: `Python 3.x`
mac下面部署

1、首先安装python3环境  brew install python3
2、设置python环境变量 
    1、用户当前目录下创建.bash_profile目录
        cd ~
        sudo su 输入密码
        touch .bash_profile
    2、设置python环境变量，python3安装目录。
        PATH="/usr/local/bin/python3:${PATH}"
3、将解压后的Instagram文件夹放到当前用户目录下
4、安装依赖环境
    将所有需要的依赖放到根目录下
    pip3 install requests 安装官方依赖（需翻墙）
5、创建log日志文件夹
6、运行程序 python3 Instagram.py user_name
