import numpy as np
import scipy.misc as sc

class Steerable:
	def __init__(self, height = 3):
		self.nbands = 4
		self.height = height

	def buildSFpyr(self, im):

		M, N = im.shape[:2]
		log_rad, angle = self.base(M, N)
		Xrcos, Yrcos = self.rcosFn(1, -0.5)
		Yrcos = np.sqrt(Yrcos)
		YIrcos = np.sqrt(1 - Yrcos*Yrcos)

		lo0mask = self.pointOp(log_rad, YIrcos, Xrcos)
		hi0mask = self.pointOp(log_rad, Yrcos, Xrcos)

		imdft = np.fft.fftshift(np.fft.fft2(im))
		lo0dft = imdft * lo0mask

		coeff = self.buildSFpyrlevs(lo0dft, log_rad, angle, Xrcos, Yrcos, self.height - 1)

		hi0dft = imdft * hi0mask
		hi0 = np.fft.ifft2(np.fft.ifftshift(hi0dft))

		coeff.append(hi0.real)

		return coeff


	def buildSFpyrlevs(self, lodft, log_rad, angle, Xrcos, Yrcos, ht):
		
		if (ht <=1):
			lo0 = np.fft.ifft2(np.fft.ifftshift(lodft))
			coeff = [lo0.real]
		
		else:
			Xrcos = Xrcos - 1

			# ==================== Orientation bandpass =======================
			himask = self.pointOp(log_rad, Yrcos, Xrcos)

			lutsize = 1024
			Xcosn = np.pi * np.array(range(-(2*lutsize+1),(lutsize+1)))/lutsize
			order = self.nbands - 1
			const = np.power(2, 2*order) * np.square(sc.factorial(order)) / (self.nbands * sc.factorial(2*order))
			Ycosn = np.sqrt(const) * np.power(np.cos(Xcosn), order)

			orients = []

			for b in range(self.nbands):
				anglemask = self.pointOp(angle, Ycosn, Xcosn + np.pi*b/self.nbands)
				banddft = np.complex(0,1) * lodft * anglemask * himask
				band = np.fft.ifft2(np.fft.ifftshift(banddft))
				orients.append(band.real)

			# ================== Subsample lowpass ============================
			dims = np.array(lodft.shape)
			
			lostart = np.ceil((dims+0.5)/2) - np.ceil((np.ceil((dims-0.5)/2)+0.5)/2) 
			loend = lostart + np.ceil((dims-0.5)/2) 

			log_rad = log_rad[lostart[0]:loend[0], lostart[1]:loend[1]]
			angle = angle[lostart[0]:loend[0], lostart[1]:loend[1]]
			lodft = lodft[lostart[0]:loend[0], lostart[1]:loend[1]]
			YIrcos = np.abs(np.sqrt(1 - Yrcos*Yrcos))
			lomask = self.pointOp(log_rad, YIrcos, Xrcos)

			lodft = lomask * lodft

			coeff = self.buildSFpyrlevs(lodft, log_rad, angle, Xrcos, Yrcos, ht-1)
			coeff.append(orients)

		return coeff


	def base(self, m, n):
		ctrm = np.ceil(float(m/2))
		ctrn = np.ceil(float(n/2))

		xv, yv = np.meshgrid(	(range(1,m+1) - ctrm)/float(m/2),\
								(range(1,n+1) - ctrm)/float(n/2))

		rad = np.sqrt(xv**2 + yv**2)
		rad[m/2-1, n/2-1] = rad[m/2-1, n/2-2]
		log_rad = np.log2(rad)

		angle = np.arctan2(yv, xv)
		
		return log_rad, angle

	def rcosFn(self, width, position):
		N = 256
		X = np.pi * np.array(range(-N-1, 2))/2/N

		Y = np.cos(X)**2
		Y[0] = Y[1]
		Y[N+2] = Y[N+1]

		X = position + 2*width/np.pi*(X + np.pi/4)
		return X, Y

	def pointOp(self, im, Y, X):
		out = np.interp(im.flatten(), X, Y)
		return np.reshape(out, im.shape)