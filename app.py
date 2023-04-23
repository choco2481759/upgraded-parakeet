from flask import Flask 
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy import create_engine
import datetime
import pyodbc
import random
import matplotlib.pyplot as plt
import os
import json




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mssql+pymssql://sa:1234@localhost:1433/BNDB'
db = SQLAlchemy(app)


conn = pyodbc.connect('DRIVER={SQL Server};SERVER=localhost;DATABASE=BNDB;UID=sa;PWD=1234')
cursor = conn.cursor()

# --------------------後台--------------------

def cleanup(session):    
    session.close() 
    
def painting(sql):
    A = db.engine.execute(sql)
    Meterial = A.fetchall()
    
    x, y = zip(*Meterial)
    
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']

    plt.figure(figsize=(10, 8))
    
    # 折線圖
    plt.bar(x, y)
    
    plt.title('銷售類型比較圖') #標題   
    plt.ylabel('營業額')       # y軸
    plt.xlabel('品名')         # x軸

    filename = 'compare.png'
    foldername = os.path.join(app.static_folder, 'images')
    filepath = os.path.join(foldername, filename)
    
    # 下載圖表
    plt.savefig(filepath)
    
    return Meterial

def tryAccount(account, pwd):
    try:
        sql = f"select count(*) from staff where Email = '{account}' and PW = '{pwd}'"
        result = db.engine.execute(sql).scalar()
    except:
        return render_template("flaskLoginError.html")
    return result    
   
    
data = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'


     
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form["account"]
        pwd = request.form["pwd"]
        result = tryAccount(account, pwd)
        if result is None or result == 0:
            return render_template("flaskLoginError.html")
        try:
            sql = f"select personnel from staff where Email = '{account}'"
            cursor.execute(sql)
            personnel = cursor.fetchone()[0]
        except Exception as err:
            raise err
        if (personnel == 'Boss'):
            return redirect(url_for('modifyMenu', thisAccount=account, thispwd=pwd))
        elif personnel == 'Staff':
            return redirect(url_for('createOrder', thisAccount=account, thispwd=pwd))

    return render_template("flaskLogin.html")

@app.route('/createOrder/<string:thisAccount>/<string:thispwd>', methods=['GET', 'POST'])
def createOrder(thisAccount, thispwd):
    result = tryAccount(thisAccount, thispwd)
    if result is None or result == 0:
        return render_template("flaskLoginError.html")
    if request.method == 'POST':
        tableID = int(request.values['tableID'])
        orderTime = (datetime.datetime.now())
        orderTimeStr = orderTime.strftime("%Y-%m-%d %H:%M:%S")
        token = ''
        for i in range(10):
            temp = random.choices(random.sample(data, 12))
            token += ''.join(temp)        
        try:
            sql = (f"execute InsertOrderMeterial '{orderTimeStr}', {tableID}, '{token}'")
            cursor.execute(sql)
            conn.commit()            
        except Exception as err:
            raise err
        try:        
            sql = "execute SelectOrderInfo"
            orderInfo = db.engine.execute(sql)     
        except Exception as err:
            raise err
        finally:            
            cleanup(db.session)
            
        return render_template("flaskCreateQRcode.html", tableID=tableID, orderInfo=orderInfo, thisAccount=thisAccount, thispwd=thispwd)                        
    try:
        sql = "select TableID from seat"
        tables = db.engine.execute(sql)              
    except Exception as err:
        raise err
    finally:
        cleanup(db.session)
        
    tables = list(tables)
    
    return render_template("flaskCreateOrder.html", **locals())
    conn.close()
    
@app.route('/orderDetail/<string:thisAccount>/<string:thispwd>', methods=['GET', 'POST'])
def orderDetail(thisAccount, thispwd):
    result = tryAccount(thisAccount, thispwd)
    if result is None or result == 0:
        return render_template("flaskLoginError.html")
    try:
        sql = "select OrderNum, tableID from OrderMeterial where PayTime is null"
        orderNum = db.engine.execute(sql)
        sql = "execute SelectOrderDetail"
        detail = db.engine.execute(sql)              
    except Exception as err:
        raise err
    finally:
        cleanup(db.session)
        
    orderNum = list(orderNum)      
    detail = list(detail)  
    
    return render_template("flaskOrderDetail.html", **locals())
    conn.close()

    
@app.route('/getCheck/<string:thisAccount>/<string:thispwd>', methods=['GET', 'POST'])
def getCheck(thisAccount, thispwd):
    result = tryAccount(thisAccount, thispwd)
    if result is None or result == 0:
        return render_template("flaskLoginError.html")
    if request.method == 'POST':
        payTime = (datetime.datetime.now())
        payTimeStr = payTime.strftime("%Y-%m-%d %H:%M:%S")
        orderNum = int(request.values['checkNum'])
        try:
            sql = (f"execute UpdatePayTime {orderNum}, '{payTimeStr}'")
            cursor.execute(sql)
            conn.commit()
        except Exception as err:
            raise err
        finally:            
            cleanup(db.session)                       
    try:
        sql = "execute SelectOrder"
        orders = db.engine.execute(sql)              
    except Exception as err:
        raise err
    finally:
        cleanup(db.session)
        
    orders = list(orders)    
    return render_template("flaskGetCheck.html", **locals())
    conn.close()

@app.route('/modifyMenu/<string:thisAccount>/<string:thispwd>', methods=['GET', 'POST'])
def modifyMenu(thisAccount, thispwd): 
    result = tryAccount(thisAccount, thispwd)
    if result is None or result == 0:
        return render_template("flaskLoginError.html")
    if request.method == 'POST':
        originalName = request.values['originalName']
        modifyName = request.values['modifyName']
        modifyPrice = int(request.values['modifyPrice'])
        try:
            sql = (f"execute UpdateMenu '{originalName}', '{modifyName}','{modifyPrice}'")
            cursor.execute(sql)            
        except:
            return render_template("flaskInsertError.html", **locals())
        finally: 
            conn.commit()
            cleanup(db.session)
    try:
        sql = "execute SelectDishType"
        DishType = db.engine.execute(sql)
        sql = "execute SelectMenu"
        menu = db.engine.execute(sql)
        sql = "execute SelectMenuPlus"
        choose = db.engine.execute(sql)        
    except Exception as err:
        raise err
    finally:
        cleanup(db.session)
    
    DishType = list(DishType)    
    menu = list(menu)
    choose = list(choose)
                
    return render_template("flaskModifyMenu.html", **locals())
    conn.close()
    
@app.route('/insertMenu/<string:thisAccount>/<string:thispwd>', methods=['GET', 'POST'])
def insertMenu(thisAccount, thispwd):
    result = tryAccount(thisAccount, thispwd)
    if result is None or result == 0:
        return render_template("flaskLoginError.html")
    if request.method == 'POST':
        insertName = request.values['insertName']
        insertPrice = request.values['insertPrice']
        typeID = int(request.values['typeID'])
        try:
            sql = (f"execute InsertMenu '{insertName}', '{insertPrice}','{typeID}'")
            cursor.execute(sql)            
        except:
            return render_template("flaskInsertError.html", **locals())
        finally:
            conn.commit()            
            cleanup(db.session)
    try:
        sql = "select * from MenuType ORDER BY TypeID"
        DishType = db.engine.execute(sql)
        sql = "execute SelectMenuPlus"
        choose = db.engine.execute(sql)
    except Exception as err:
        raise err
    finally:
        cleanup(db.session)
        
    DishType = list(DishType)
    choose = list(choose)
            
    return render_template("flaskInsertMenu.html", **locals()) 

@app.route('/analyze/<string:thisAccount>/<string:thispwd>', methods=['GET', 'POST'])
def analyze(thisAccount, thispwd):
    result = tryAccount(thisAccount, thispwd)
    if result is None or result == 0:
        return render_template("flaskLoginError.html")
    if request.method == 'POST':
        T = ""
        Y = request.values['year']
        M = request.values['month']
        D = request.values['day']

        try:
            sql = f"Execute calRevenue '{Y}', '{M}', '{D}' "
            Meterial = painting(sql)
        except:
            return render_template('flaskAnalyzeError.html', **locals())      
            
        return render_template('flaskAnalyzeResult.html', **locals())                       
                      
    return render_template("flaskAnalyze.html", **locals())

@app.route('/analyzeDetail/<string:thisAccount>/<string:thispwd>')
def analyzeDetail(thisAccount, thispwd):
    result = tryAccount(thisAccount, thispwd)
    if result is None or result == 0:
        return render_template("flaskLoginError.html")
    
    T = request.args.get('type')
    Y = request.args.get('year')
    M = request.args.get('month')
    D = request.args.get('day')

    
    #try:
    sql = f"Execute calRevenueDetail '{T}', '{Y}', '{M}', '{D}'"                
    Meterial = painting(sql)
    #except:
    #    return render_template('flaskAnalyzeError.html')  
   
    return render_template('flaskAnalyzeResult.html', **locals())  

# --------------------前台--------------------

@app.route('/menu/<int:thisOrderNum>/<int:thisTableID>/<string:thisToken>', methods=['GET', 'POST'])
def menu(thisOrderNum, thisTableID, thisToken):
    
#if request.method == 'POST':              
    cartListStr = request.form['cartList']        
    total = int(request.form['total'])
    cartList = json.loads(cartListStr) 
        #try:            
    for cart in cartList:
        sql = f"select DisherID from menu where dishes = '{cart['name']}'"
        cursor.execute(sql)
        disherID = cursor.fetchone()[0]
        quantity = int(cart['itemQuantity'])                
        sql = f"execute InsertOrderRecord {thisOrderNum}, {disherID}, {quantity}, {thisTableID}"
        cursor.execute(sql)
        conn.commit()
        #except Exception as err:
            #raise err
        #try:            
        sql = f"execute SelectCartList {thisOrderNum}"
        sumCartList = db.engine.execute(sql)
        sql = f"execute calTotal {thisOrderNum}"
        cursor.execute(sql)
        sumTotal = cursor.fetchone()[0]
        #except Exception as err:
        #    raise err
        #finally:       
        cleanup(db.session)  
        
    sumCartList =list(sumCartList)
    
    return render_template("flaskOrder.html", orderNum=thisOrderNum, cartList=sumCartList, tableID=thisTableID, total=sumTotal, token=thisToken)
    conn.close()
    
    #try:
    sql = f"select orderNum from OrderMeterial where token = '{thisToken}'"
    cursor.execute(sql)
    checkOrderNum = cursor.fetchone()[0]
    #except Exception:
        #return render_template("flaskMenuError.html")
    
    if (thisOrderNum != checkOrderNum):
        return render_template("flaskMenuError.html")    
    else:                   
        #try:
        sql = "execute SelectDishType"
        DishType = db.engine.execute(sql)
        sql = "execute SelectMenu"
        menu = db.engine.execute(sql)
        sql = "execute SelectSideDish"
        sideDish = db.engine.execute(sql)
        sql = "select TableID from dbo.seat"
        tables = db.engine.execute(sql)
        #except Exception as err:
        #    raise err    
        
    DishType = list(DishType)    
    menu = list(menu)
    sideDish = list(sideDish)
    tables = list(tables) 
            
    return render_template("flaskMenu.html", **locals())
    conn.close()

@app.route('/checkOrder/<int:thisOrderNum>/<int:thisTableID>/<string:thisToken>')
def checkorder(thisOrderNum, thisTableID, thisToken):
    try:            
        sql = f"execute SelectCartList {thisOrderNum}"
        sumCartList = db.engine.execute(sql)
        sql = f"execute calTotal {thisOrderNum}"
        cursor.execute(sql)
        sumTotal = cursor.fetchone()[0]
    except Exception as err:
        raise err
    finally:       
        cleanup(db.session)  
    
    sumCartList =list(sumCartList)
    
    return render_template("flaskOrder.html", orderNum=thisOrderNum, cartList=sumCartList, tableID=thisTableID, total=sumTotal, token=thisToken)
    




if __name__ == "__main__":
    app.run(port="50001")