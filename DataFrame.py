import pandas as pd
import numpy as np  

class DF:

	def __init__(self, cleaned_data):
		self.df = pd.DataFrame(cleaned_data, columns=list(cleaned_data.keys()))
		self.df = self.df.set_index('time received')

	def __getitem__(self, column):
		return self.df[column]

	def restart(self):
		self.df = pd.DataFrame(columns=['time received', 'energy'])

	def tail(self, n):
		return self.df.tail(n)

	def to_string(self):
		print (self.df.to_string())
