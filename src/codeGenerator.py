#!/usr/bin/python

from copyreg import constructor
import sys
import argparse
import re
import logging

class CodeGenerator(Object):
	symboleTable = []
	compilationUnits=[]

	def addUnite(self,unite):
		self.compilationUnits.append(unite)
	

class CompilationUnite(Object):
	def stringify(symbols):
		return False

class debutProg(CompilationUnite):

	def stringify(symbols):
		return "debutProg()"
		
class reserver(CompilationUnite):
	params =[]
	def constructor(self,n):
		self.params.append(n)
	
	def stringify(self,symbols):
		unite = "reserver("
		for param in self.params:
			unite+=str(symbols[param])+","
		if unite[-1]==",":
			unite[-1]=")"
		else:
			unite+=")"
		return unite



class moins(CompilationUnite):
	params =[]
	
	def stringify(self,symbols):
		unite = "moins()"
		return unite

class sous(CompilationUnite):
	params =[]
	
	def stringify(self,symbols):
		unite = "sous()"
		return unite

class add(CompilationUnite):
	params =[]
	
	def stringify(self,symbols):
		unite = "add()"
		return unite

class mult(CompilationUnite):
	params =[]
	
	def stringify(self,symbols):
		unite = "mult()"
		return unite

class div(CompilationUnite):
	params =[]
	
	def stringify(self,symbols):
		unite = "div()"
		return unite
#classes supp pour procédural

class empilerAdd(CompilationUnite):
	params =[]
	def constructor(self,n):
		self.params.append(n)
	
	def stringify(self,symbols):
		unite = "empilerAdd("
		for param in self.params:
			unite+=str(symbols[param])+","
		if unite[-1]==",":
			unite[-1]=")"
		else:
			unite+=")"
		return unite
