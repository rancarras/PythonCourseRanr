#c3v
from sys import maxsize
 
from numpy import *
from scipy.stats import vonmises
import pylab

@profile
def rp(N2, q1):
    N1 = 1.0
    q2 = arcsin(N1*sin(q1)/N2)
    return (N2*cos(q1) - N1*cos(q2))/(N2*cos(q1) + N1*cos(q2))

def rs(N2, q1):
    N1 = 1.0
    q2 = arcsin(N1*sin(q1)/N2)
    return (N1*cos(q1) - N2*cos(q2))/(N1*cos(q1) + N2*cos(q2))

def L(N2, q1):
    Np = 0.5*(1.0 + N2)
    Lxx = (1.0 - rp(N2, q1)) * cos(q1)
    Lyy = 1.0 + rs(N2, q1)
    Lzz = (1.0 + rp(N2, q1)) * sin(q1) * (1.0/Np)**2
    return (Lxx, Lyy, Lzz)

def odf(theta, phi, psi, theta0, sigmaTheta, phi0, sigmaPhi):
    odftheta = exp(-(theta - theta0)**2/(2*sigmaTheta**2))
    wrapped_phi = vonmises.pdf(phi, 1./sigmaPhi**2, phi0)
    return odftheta*wrapped_phi

# setup
pylab.rc('font', size=7)
fig, axs = pylab.subplots(3, 3, figsize=(6.75, 6.75), subplot_kw = {'projection':'polar'})
fig.delaxes(axs[2,2])
theta0 = radians(30.)
sigmaTheta = radians(25.)
phi0 = radians(90.)
sigmaPhi = radians(25.)
steps = 50
theta, phi, psi = meshgrid(linspace(0, pi, steps), linspace(0, 2*pi, 2*steps), linspace(0, 2*pi, 2*steps))
aac = 3.0
bbc = 3.8
ccc = 1.
Phi = linspace(-pi, pi, 100)
global maxs
maxs = []

# beam angles
theta_vis = radians(70.)
theta_IR = radians(55.)
theta_SFG = radians(68.)

# calcite refractive index data
N_vis = N_SFG = 1.5
N_IR = 1.5

# local field corrections
L_SFG = L(N_SFG, theta_SFG)
L_vis = L(N_vis, theta_vis)
L_IR = L(N_IR, theta_IR)

# direction cosine matrix
R1 = array([[cos(psi), -sin(psi), 0], [sin(psi), cos(psi), 0], [0, 0, 1]], dtype=object)
R2 = array([[cos(theta), 0, sin(theta)], [0, 1, 0], [-sin(theta), 0, cos(theta)]], dtype=object)
R3 = array([[cos(phi), -sin(phi), 0], [sin(phi), cos(phi), 0], [0, 0, 1]], dtype=object)
DCM = dot(R3, dot(R2, R1))

# hyperpolarizability in the methyl frame
beta = array([[[0,0,aac], [0,0,0], [0,0,0]],
    [[0,0,0], [0,0,bbc], [0,0,0]],
    [[0,0,0], [0,0,0], [0,0,ccc]]])

# we need all elements of chi2 in the surface frame, in terms of the ODF parameters
# e.g. chi2xxx(params) = int_Omega alpha2xxx(Omega) * f(Omega, params) * dOmega

# project onto surface frame (the 'primed' coordinate system)
norm = sum(odf(theta, phi, psi, theta0, sigmaTheta, phi0, sigmaPhi)*sin(theta))
surface = zeros([3,3,3])
for i in [0, 1, 2]:
    for j in [0, 1, 2]:
        for k in [0, 1, 2]:
            temp = 0
            for l in [0, 1, 2]:
                for m in [0, 1, 2]:
                    for n in [0, 1, 2]:
                        temp += DCM[i,l]*DCM[j,m]*DCM[k,n]*beta[l,m,n]
            
            # integration
            surface[i,j,k] = sum(temp*odf(theta, phi, psi, theta0, sigmaTheta, phi0, sigmaPhi)*sin(theta))/norm

# rotation matrix from HIR1051
R = array([[cos(Phi), sin(Phi), 0], [-sin(Phi), cos(Phi), 0], [0, 0, 1]], dtype=object)

# project onto laboratory frame
lab = zeros([3,3,3], dtype=object)
for i in [0, 1, 2]:
    for j in [0, 1, 2]:
        for k in [0, 1, 2]:
            temp = 0
            for l in [0, 1, 2]:
                for m in [0, 1, 2]:
                    for n in [0, 1, 2]:
                        temp += R[i,l]*R[j,m]*R[k,n]*surface[l,m,n]
            lab[i,j,k] = temp

@profile
def graph(scheme, elements, location):
    chi2 = 0.
    for e in elements:
        i, j, k = e
        chi2 += L_SFG[i]*L_vis[j]*L_IR[k]*lab[i,j,k]
    norm = max(abs(chi2)**2)
    # ax2.plot(Phi, abs(chi2)**2/norm, 'g-')
    axs[location[0], location[1]].plot(Phi[chi2>0], abs(chi2[chi2>0])**2, 'k-')
    axs[location[0], location[1]].plot(Phi[chi2<0], abs(chi2[chi2<0])**2, 'k-')
    axs[location[0], location[1]].set_title(scheme, fontweight='bold', color='b')

    maxs.append(max(abs(chi2)**2))

graph('sss', [(1,1,1)], (0,0))
graph('sps', [(1,0,1), (1,2,1)], (2,1))
graph('ssp', [(1,1,0), (1,1,2)], (0,1))
graph('spp', [(1,0,0), (1,0,2), (1,2,0), (1,2,2)], (1,0))
graph('pss', [(0,1,1), (2,1,1)], (1,1))
graph('pps', [(0,0,1), (0,2,1), (2,0,1), (2,2,1)], (0,2))
graph('psp', [(0,1,0), (0,1,2), (2,1,0), (2,1,2)], (2,0))
graph('ppp', [(0,0,0), (0,0,2), (0,2,0,), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)], (1,2))

# pretty
fig.set_tight_layout(True)
for i in range(3):
    for j in range(3):
        # axs[i,j].set_rlim(0, max(maxs))
        axs[i,j].set_rticks([])
        axs[i,j].set_xticks(arange(0, 2*pi, 2*pi/8.))
        axs[i,j].set_xticklabels(['0$^\circ$', '45$^\circ$', '', '135$^\circ$', '180$^\circ$', '225$^\circ$', '270$^\circ$', '315$^\circ$'])
pylab.savefig('fit.png', dpi=600)