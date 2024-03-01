import math
unsorted = [3,1,4,8,5,3]

def mergeSort(data):
	if len(data) == 1 or len(data) == 0:
		return data

	midindex = int(len(data)//2)
	upper = data[midindex:]
	upper = mergeSort(upper)

	lower = data[:midindex]
	lower = mergeSort(lower)

	i, j, k = 0, 0, 0
	while i<len(lower) and j<len(upper):
		if lower[i] <= upper[j]:
			data[k] = lower[i]
			i += 1
		else:
			data[k] = upper[j]
			j += 1
		k += 1

	while i<len(lower):
		data[k] = lower[i]
		i += 1
		k += 1

	while j<len(upper):
		data[k] = upper[j]
		j += 1
		k += 1
	return data

print(mergeSort(unsorted))