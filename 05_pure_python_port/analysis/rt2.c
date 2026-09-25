#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define NR_PI 3.141592653589793
#define SWAP(a,b) {double t=(a);(a)=(b);(b)=t;}
// variant R: true rotation recurrence
void four1R(double data[], unsigned long nn, int isign){
  unsigned long n,mmax,m,j,istep,i; double wtemp,wr,wpr,wpi,wi,theta,tempr,tempi;
  n=nn<<1; j=1;
  for(i=1;i<n;i+=2){ if(j>i){ SWAP(data[j],data[i]); SWAP(data[j+1],data[i+1]); }
    m=n>>1; while(m>=2 && j>m){ j-=m; m>>=1; } j+=m; }
  mmax=2;
  while(n>mmax){ istep=mmax<<1; theta=isign*(2.0*NR_PI/mmax);
    wtemp=sin(0.5*theta); wpr=-2.0*wtemp*wtemp; wpi=sin(theta); wr=1.0; wi=0.0;
    for(m=1;m<mmax;m+=2){ for(i=m;i<=n;i+=istep){ j=i+mmax;
        tempr=wr*data[j]-wi*data[j+1]; tempi=wr*data[j+1]+wi*data[j];
        data[j]=data[i]-tempr; data[j+1]=data[i+1]-tempi;
        data[i]+=tempr; data[i+1]+=tempi; }
      wtemp=wr; wr=wr+wr*wpr-wi*wpi; wi=wi+wi*wpr+wtemp*wpi; }
    mmax=istep; }
}
int main(void){
  double d[33],orig[33]; size_t i; unsigned long nn;
  for(nn=2;nn<=8;nn+=2){
    for(i=1;i<=2*nn;i++) d[i]=((double)rand()/RAND_MAX);
    for(i=1;i<=2*nn;i++) orig[i]=d[i];
    four1R(d,nn,1); four1R(d,nn,-1);
    double mx=0; for(i=1;i<=2*nn;i++){ double e=fabs(d[i]-orig[i]*nn); if(e>mx) mx=e; }
    printf("nn=%2lu variantR roundtrip maxerr=%.3e\n", nn, mx);
  }
  return 0;
}
