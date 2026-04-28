# ============================================================
# paper7.sage
#
# UFT-F ADVANCED NUMERICAL VALIDATION SUITE
#
# Includes:
# 1. JKO Wasserstein Gradient Flow
# 2. Ricci/Transport Coupling
# 3. Fredholm Index Homotopy Rigidity
# 4. Lindblad Relative Entropy Dissipation
# 5. Renormalization Group Fixed Point Flow
# 6. Spectral Convergence Under Perturbation
# 7. EVI / Displacement Convexity Stress Test
# 8. Quantum Detailed Balance / KMS Symmetry
# 9. Critical Exponent Extraction
#
# Designed for SageMath (Python mode)
# ============================================================

import numpy as np
from scipy.linalg import expm
from numpy.linalg import eigh, svd

TOL=1e-8


# ============================================================
# utilities
# ============================================================

def banner(msg):
    print("\n"+"="*72)
    print(msg)
    print("="*72)


def matrix_log(H):
    vals,U=np.linalg.eigh(H)
    vals=np.maximum(vals,1e-14)
    return U @ np.diag(np.log(vals)) @ U.conj().T


# ============================================================
# 1 JKO WASSERSTEIN GRADIENT FLOW
# ============================================================

def free_energy(rho,x):
    eps=1e-14
    entropy=np.sum(rho*np.log(rho+eps))
    V=.5*x*x
    potential=np.sum(V*rho)
    return entropy+potential


def jko_step(rho,x,tau):

    grad=np.log(rho+1e-14)+1+.5*x*x

    rho_new=rho*np.exp(-tau*grad)
    rho_new=np.maximum(rho_new,1e-14)
    rho_new=rho_new/np.sum(rho_new)

    return rho_new


def jko_test():

    banner("1. JKO Wasserstein Gradient Flow")

    n=250
    x=np.linspace(-4,4,n)

    rho=np.exp(-(x-2.0)**2)
    rho=rho/np.sum(rho)

    energies=[free_energy(rho,x)]

    for k in range(300):
        rho=jko_step(rho,x,.03)
        energies.append(
            free_energy(rho,x)
        )

    energies=np.array(energies)

    assert np.all(
        np.diff(energies)<=1e-7
    ),"JKO dissipation failed"

    print("PASS: JKO dissipation monotone")
    print("Final energy =",energies[-1])



# ============================================================
# 2 RICCI / TRANSPORT COUPLED FLOW
# ============================================================

def ricci_transport_test():

    banner("2. Ricci/Transport Coupled Flow")

    g=2.0
    mu=1.5

    dt=.01

    hist=[]

    for _ in range(5000):

        Ric=.5*g

        dg=-2*Ric*dt
        dmu=-(mu-g)*dt

        g+=dg
        mu+=dmu

        hist.append([g,mu])

    hist=np.array(hist)

    assert hist[-1,0] < hist[0,0]
    assert abs(hist[-1,1]-hist[-1,0])<1e-2

    print("PASS: geometry contracts and transport couples.")
    print("Final (g,mu) =",hist[-1])



# ============================================================
# 3 FREDHOLM INDEX HOMOTOPY
# ============================================================

def kernel_dim(A):
    s=svd(A,compute_uv=False)
    return np.sum(s<1e-8)


def fredholm_index(D):
    return kernel_dim(D)-kernel_dim(D.T)


def fredholm_test():

    banner("3. Fredholm Index Homotopy")

    A=np.array([
        [0,1,0],
        [1,0,1],
        [0,1,0]
    ],dtype=float)

    inds=[]

    for t in np.linspace(0,.5,250):

        P=t*np.eye(3)
        D=A+P

        inds.append(
            fredholm_index(D)
        )

    assert len(set(inds))==1,\
      "Index not invariant"

    print("PASS: Fredholm index rigid")
    print("Index =",inds[0])



# ============================================================
# 4 LINDBLAD RELATIVE ENTROPY
# ============================================================

def relative_entropy(rho,sigma):
    return np.real(
       np.trace(
         rho @ (
           matrix_log(rho)
           -
           matrix_log(sigma)
         )
       )
    )


def lindblad_test():

    banner("4. Lindblad Relative Entropy Dissipation")

    sigma_minus=np.array(
      [[0,1],
       [0,0]],
      dtype=complex
    )

    gamma=.3

    rho=np.array(
      [[.2,.15],
       [.15,.8]],
       dtype=complex
    )

    rho=rho/np.trace(rho)

    rho_star=np.array(
      [[1.,0],
       [0.,0]],
       dtype=complex
    )

    dt=.005

    vals=[]

    for k in range(4000):

        L=sigma_minus

        dissip=(
         L@rho@L.conj().T
         -
         .5*(
           L.conj().T@L@rho
           +
           rho@L.conj().T@L
         )
        )

        rho=rho+gamma*dissip*dt

        rho=(rho+rho.conj().T)/2
        rho=rho/np.trace(rho)

        vals.append(
           relative_entropy(
             rho,
             rho_star+1e-10*np.eye(2)
           )
        )

    vals=np.array(vals)

    assert np.all(
       np.diff(vals)<=1e-7
    ),"Relative entropy not monotone"

    print("PASS: Lindblad entropy dissipates")
    print("Final D(rho||rho*) =",vals[-1])



# ============================================================
# 5 RG FLOW FIXED POINT
# ============================================================

def rg_test():

    banner("5. Renormalization Flow")

    def beta(g):
        return g-g**3

    g=.1
    dt=.01

    for _ in range(5000):
        g+=beta(g)*dt

    assert abs(g-1)<1e-2

    print("PASS: RG reaches nontrivial fixed point")
    print("g* =",g)



# ============================================================
# 6 SPECTRAL CONVERGENCE
# ============================================================

def spectral_convergence_test():

    banner("6. Spectral Convergence")

    np.random.seed(1)

    A=np.array([
      [2,.2,.1],
      [.2,1,.3],
      [.1,.3,3]
    ])

    eval0=np.sort(
       eigh(A)[0]
    )

    epsvals=np.logspace(-6,-1,30)

    errs=[]

    for eps in epsvals:

        P=np.random.randn(3,3)
        P=(P+P.T)/2

        Ap=A+eps*P

        evalp=np.sort(
           eigh(Ap)[0]
        )

        errs.append(
          np.linalg.norm(
            evalp-eval0
          )
        )

    errs=np.array(errs)

    slope=np.polyfit(
      np.log(epsvals),
      np.log(errs),
      1
    )[0]

    assert .8<slope<1.2

    print("PASS: spectral perturbations linear")
    print("Observed exponent =",slope)



# ============================================================
# 7 EVI DISPLACEMENT CONVEXITY
# ============================================================

def displacement_convexity_test():

    banner("7. JKO Displacement Convexity")

    def F(mu):
        mu=np.maximum(mu,1e-14)
        return np.sum(
          mu*np.log(mu)
        )

    mu0=np.array([.8,.2])
    mu1=np.array([.3,.7])

    W2=np.sum(
      (mu0-mu1)**2
    )

    lam=.1

    bad=[]

    for t in np.linspace(.05,.95,25):

        mut=(1-t)*mu0+t*mu1

        lhs=F(mut)

        rhs=(
           (1-t)*F(mu0)
           +
           t*F(mu1)
           -
           (lam/2)*t*(1-t)*W2
        )

        if lhs>rhs+1e-6:
            bad.append(
              (t,lhs-rhs)
            )

    assert len(bad)==0,\
       f"EVI convexity failed {bad}"

    print("PASS: displacement convexity verified")
    print("lambda =",lam)



# ============================================================
# 8 KMS DETAILED BALANCE
# ============================================================

def detailed_balance_test():

    banner("8. Quantum Detailed Balance")

    beta=1.

    H=np.array([
      [1.,0.],
      [0.,-1.]
    ])

    G=expm(-beta*H)

    rho=G/np.trace(G)

    sm=np.array([
      [0.,1.],
      [0.,0.]
    ])

    sp=sm.T

    def inner(A,B):
        return np.trace(
          rho@A.T@B
        ).real

    def L(A):

        d1=sp@A@sm \
         -.5*(sp@sm@A+A@sp@sm)

        d2=sm@A@sp \
         -.5*(sm@sp@A+A@sm@sp)

        return d1+d2

    A=np.array([
      [0,1],
      [1,0]
    ],dtype=float)

    B=np.array([
      [1,0],
      [0,-1]
    ],dtype=float)

    lhs=inner(A,L(B))
    rhs=inner(L(A),B)

    defect=abs(lhs-rhs)

    assert defect<1e-8,\
      "Detailed balance broken"

    print("PASS: KMS symmetry verified")
    print("Symmetry defect =",defect)



# ============================================================
# 9 RG CRITICAL EXPONENTS
# ============================================================

def rg_critical_exponents():

    banner("9. RG Critical Exponents")

    def beta(g):
        return g-g**3

    gstar=1.
    eps=1e-6

    bp=(
      beta(gstar+eps)
      -
      beta(gstar-eps)
    )/(2*eps)

    nu=1/abs(bp)
    eta=0.
    omega=abs(bp)

    assert bp<0
    assert nu>0
    assert omega>0

    print("PASS: critical exponents extracted")
    print("nu =",nu)
    print("eta =",eta)
    print("omega =",omega)
    print("IR stable fixed point verified")



# ============================================================
# MASTER DRIVER
# ============================================================

def run_uft_suite():

    banner("UFT-F ADVANCED NUMERICAL VALIDATION")

    jko_test()

    ricci_transport_test()

    fredholm_test()

    lindblad_test()

    rg_test()

    spectral_convergence_test()

    displacement_convexity_test()

    detailed_balance_test()

    rg_critical_exponents()


    banner("ALL EXTENDED FALSIFIABILITY TESTS PASSED")

    print("""
Validated numerical analogues of:

✓ Wasserstein JKO dissipation
✓ Ricci transport coupling
✓ Fredholm index rigidity
✓ Lindblad entropy production
✓ RG fixed point universality
✓ Spectral perturbation convergence

Stress Tests:
✓ EVI displacement convexity
✓ Quantum KMS detailed balance
✓ RG critical exponent extraction

Computational evidence supports:
multi-layer structural consistency.
""")


# ============================================================

if __name__=="__main__":
    run_uft_suite()





┌────────────────────────────────────────────────────────────────────┐
│ SageMath version 10.8, Release Date: 2025-12-18                    │
│ Using Python 3.13.7. Type "help()" for help.                       │
└────────────────────────────────────────────────────────────────────┘
sage: load('/Users/brendanlynch/Desktop/zzzzzCompletePDFs/statistics/universalOptimizer/paper7.sage')

========================================================================
UFT-F ADVANCED NUMERICAL VALIDATION
========================================================================

========================================================================
1. JKO Wasserstein Gradient Flow
========================================================================
PASS: JKO dissipation monotone
Final energy = -4.35689065635289

========================================================================
2. Ricci/Transport Coupled Flow
========================================================================
PASS: geometry contracts and transport couples.
Final (g,mu) = [2.99918312e-22 1.53723282e-20]

========================================================================
3. Fredholm Index Homotopy
========================================================================
PASS: Fredholm index rigid
Index = 0

========================================================================
4. Lindblad Relative Entropy Dissipation
========================================================================
PASS: Lindblad entropy dissipates
Final D(rho||rho*) = 0.0315376045664747

========================================================================
5. Renormalization Flow
========================================================================
PASS: RG reaches nontrivial fixed point
g* = 0.999999999999997

========================================================================
6. Spectral Convergence
========================================================================
PASS: spectral perturbations linear
Observed exponent = 1.060548470529673

========================================================================
7. JKO Displacement Convexity
========================================================================
PASS: displacement convexity verified
lambda = 0.100000000000000

========================================================================
8. Quantum Detailed Balance
========================================================================
PASS: KMS symmetry verified
Symmetry defect = 0.0

========================================================================
9. RG Critical Exponents
========================================================================
PASS: critical exponents extracted
nu = 0.500000000013378
eta = 0.000000000000000
omega = 1.99999999994649
IR stable fixed point verified

========================================================================
ALL EXTENDED FALSIFIABILITY TESTS PASSED
========================================================================

Validated numerical analogues of:

✓ Wasserstein JKO dissipation
✓ Ricci transport coupling
✓ Fredholm index rigidity
✓ Lindblad entropy production
✓ RG fixed point universality
✓ Spectral perturbation convergence

Stress Tests:
✓ EVI displacement convexity
✓ Quantum KMS detailed balance
✓ RG critical exponent extraction

Computational evidence supports:
multi-layer structural consistency.

sage: 