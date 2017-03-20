

class Course(object):
    course_name = "Python 自动化"
    period = "7m"
    outline = "sdfsfsdfsfsdf"
    test = 321
    print("in course")

class SchoolMember(object):
    members = 0
    test = 123
    print("in Schoolmember")
    def __init__(self, name,age,sex):
        self.name = name
        self.age = age
        self.sex = sex

        SchoolMember.members +=1
        # 每次子类实例化时，执行构造函数里的SchoolMember.members +=1  将members存到类变量里
        # self.members 是 子类实例化调用members后存在新的变量
        print("初始化了一个新学校成员",self.name)

    def tell(self):
        info = '''
        -----info of %s -------
        name: %s
        age : %s
        sex : %s
        '''%(self.name,self.name,self.age,self.sex)
        print(info)

    def __del__(self):#析构方法
        print("%s 被开除了"% self.name)
        SchoolMember.members -=1

class Teacher(SchoolMember):

    def __init__(self,name,age,sex,salary):
        SchoolMember.__init__(self,name,age,sex )
        #self.name = name #t.name =name
        self.salary = salary


    def teaching(self,course):
        print("%s is teaching %s"%(self.name,course))


class Student(SchoolMember,Course):
    def __init__(self,name,age,sex,grade,teacher ):
        SchoolMember.__init__(self,name,age,sex )
        #self.name = name #t.name =name
        self.grade = grade
        self.my_teacher =  teacher



    def pay_tuition(self,amount):
        self.paid_tuition = amount
        print("stduent %s has paid tution amount %s" %(self.name,amount))


t = Teacher("Alex",22,"F",3000)
s = Student("Liuhao",24,"M","pys16", t)
# s2 = Student("YanShuai",46,"F","pys26")
# s4 = Student("NiNing",32,"F","pys26")
print("my teacher",s.my_teacher.name)

s.my_new_teacher = t
print(SchoolMember.members)
print(t.members)
print(SchoolMember.members)
print(s.members)


#del s4
# t.tell()
# s.tell()
# s2.tell()

# t.teaching("python")
# s.pay_tuition(11000)
# print(SchoolMember.members)


# print(s.course_name,s.outline)
# print("test:",s.test)

