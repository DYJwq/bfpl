本BFPL1.0语言通过Python3编写,接近汇编,有完备图灵.
介绍:
#: 注释
D name expr : 定义名为name的变量,初始值为expr
N name : 打印name的值
M name : 定义图灵机名称为name
S ptr_name TM : 设置ptr_name指向TM(TM为图灵机)
+ ptr expr : 使ptr指向的值加expr
- ptr expr : 使ptr指向的值减expr
R ptr expr : 使ptr指针右移expr位 R:right
L ptr expr : 使ptr指针左移expr位 L:left
O ptr : 输出ptr指向的值 O:output
I v : 输入变量 v 的值(一个字符)
J Label : 跳转到Label标签
JZ v Label : 如果v为0则跳转到Label标签
JNZ v Label : 如果v不为0则跳转到Label标签
H : 停机
E v expr : 使v等于expr
[] : 如果v不为0则执行[]中的指令
其他指令都无用,抛出SyntaxError:未知指令错误
可能的报错:
SyntaxError:未知指令错误
SyntaxError:变量未定义错误
SyntaxError:变量未初始化错误
SyntaxError:图灵机未定义错误

请先运行 ins Python.bat 脚本安装Python3环境

接下来是实例:
M tape;
S p tape;
+ p 5;          # 纸带值设为 5
[ p;            # 循环开始，条件 p 指向的值 != 0
    O p;        # 输出当前值（字符形式）
    - p 1;      # 值减 1
];              # 循环结束
H;