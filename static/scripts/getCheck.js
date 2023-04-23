const submitCheck = document.getElementById('submitCheck')
const orderNum = document.getElementById('oederNumInput')
const modal = document.getElementById('exampleModal')

window.addEventListener('load', function (){ 
    modal.addEventListener('show.bs.modal', function (e) {        
        let btn = e.relatedTarget;                
        orderNum.value = btn.value;   
    })

    submitCheck.addEventListener('click', function(){
        window.alert("付費時間更新成功！");
        window.location.href = window.location.href;                           
    })    
})