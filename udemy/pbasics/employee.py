#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 05:59:59 2021

@author: archanajegan
"""


class employee:
    def __init__(self, name="Tim", emp_id="E0001", exp=5, dept="R&D"):
        self.name = name
        self.emp_id = emp_id
        self.exp = exp
        self.dept = dept

        print("Employee {} is created".format(self.name))
    
    def calcSalary(self):
        if self.exp < 5 and self.dept == "R&D":
            self.salary = 200000
        else:
            self.salary = 80000
    
    def empDesc(self):
        print("Employee {} from {} department working with us for {} years".format(self.name, self.dept, self.exp))
        
    

empl = employee()
empl.calcSalary()
print(empl.salary)
empl.empDesc()
