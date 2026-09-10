//===== 0x10001000 =====

/* public: __thiscall AboutBQ::AboutBQ(void) */

AboutBQ * __thiscall AboutBQ::AboutBQ(AboutBQ *this)

{
                    /* 0x1000  1  ??0AboutBQ@@QAE@XZ */
  return this;
}

//===== 0x1000100e =====

/* public: __thiscall AboutBQ::~AboutBQ(void) */

void __thiscall AboutBQ::~AboutBQ(AboutBQ *this)

{
                    /* 0x100e  29  ??1AboutBQ@@QAE@XZ */
  return;
}

//===== 0x10001019 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: float __thiscall AboutBQ::productVersion(void)const  */

float __thiscall AboutBQ::productVersion(AboutBQ *this)

{
                    /* 0x1019  313  ?productVersion@AboutBQ@@QBEMXZ */
  return _DAT_100380e8;
}

//===== 0x1000102a =====

/* public: char const * __thiscall AboutBQ::productPatents(void)const  */

char * __thiscall AboutBQ::productPatents(AboutBQ *this)

{
                    /* 0x102a  312  ?productPatents@AboutBQ@@QBEPBDXZ */
  return PTR_s_Pat__6_208_941_B1_and_5_273_632_1003f16c;
}

//===== 0x1000103a =====

/* public: char const * __thiscall AboutBQ::productName(void)const  */

char * __thiscall AboutBQ::productName(AboutBQ *this)

{
                    /* 0x103a  311  ?productName@AboutBQ@@QBEPBDXZ */
  return PTR_s_BaseQual__Cimarron_Software_Inc__1003f190;
}

//===== 0x1000104a =====

/* public: int __thiscall AboutBQ::numProcedures(void)const  */

int __thiscall AboutBQ::numProcedures(AboutBQ *this)

{
                    /* 0x104a  293  ?numProcedures@AboutBQ@@QBEHXZ */
  return 3;
}

//===== 0x1000105a =====

/* public: char const * __thiscall AboutBQ::procedureName(int)const  */

char * __thiscall AboutBQ::procedureName(AboutBQ *this,int param_1)

{
                    /* 0x105a  310  ?procedureName@AboutBQ@@QBEPBDH@Z */
  if ((param_1 < 0) || (3 < (uint)param_1)) {
    param_1 = 3;
  }
  return (&PTR_s_Base__Calling_1003f0f0)[param_1];
}

//===== 0x10001084 =====

void FUN_10001084(void)

{
  FUN_1000108e();
  return;
}

//===== 0x1000108e =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1000108e(void)

{
  _DAT_10041a28 = acos(-1.0);
  return;
}

//===== 0x100010b0 =====

/* public: class AboutBQ & __thiscall AboutBQ::operator=(class AboutBQ const &) */

AboutBQ * __thiscall AboutBQ::operator=(AboutBQ *this,AboutBQ *param_1)

{
                    /* 0x10b0  42  ??4AboutBQ@@QAEAAV0@ABV0@@Z */
  *this = *param_1;
  return this;
}

//===== 0x100010d0 =====

/* public: short __thiscall ShftVect::s(int)const  */

short __thiscall ShftVect::s(ShftVect *this,int param_1)

{
                    /* 0x10d0  345  ?s@ShftVect@@QBEFH@Z */
  return *(short *)(this + param_1 * 2 + -2);
}

//===== 0x100010f0 =====

/* public: class ShftVect & __thiscall ShftVect::operator=(class ShftVect const &) */

ShftVect * __thiscall ShftVect::operator=(ShftVect *this,ShftVect *param_1)

{
  undefined4 uVar1;
  
                    /* 0x10f0  54  ??4ShftVect@@QAEAAV0@ABV0@@Z */
  uVar1 = *(undefined4 *)(param_1 + 4);
  *(undefined4 *)this = *(undefined4 *)param_1;
  *(undefined4 *)(this + 4) = uVar1;
  return this;
}

//===== 0x10001110 =====

/* public: void __thiscall ObsInpSpec::resWaxNWane(int,int) */

void __thiscall ObsInpSpec::resWaxNWane(ObsInpSpec *this,int param_1,int param_2)

{
                    /* 0x1110  338  ?resWaxNWane@ObsInpSpec@@QAEXHH@Z */
  *(int *)(this + 200) = param_1;
  *(int *)(this + 0xcc) = param_2;
  return;
}

//===== 0x10001140 =====

/* public: void __thiscall ObsInpSpec::ratio(int,int,float,int,int,int) */

void __thiscall
ObsInpSpec::ratio(ObsInpSpec *this,int param_1,int param_2,float param_3,int param_4,int param_5,
                 int param_6)

{
                    /* 0x1140  328  ?ratio@ObsInpSpec@@QAEXHHMHHH@Z */
  *(float *)(this + param_2 * 4 + param_1 * 0x18 + 0x68) = param_3;
  *(int *)(this + 100) = param_4;
  *(int *)(this + param_1 * 0x18 + 0x78) = param_5;
  *(int *)(this + param_1 * 0x18 + 0x7c) = param_6;
  return;
}

//===== 0x10001190 =====

/* public: void __thiscall ObsInpSpec::setMeasurementRange(int,int) */

void __thiscall ObsInpSpec::setMeasurementRange(ObsInpSpec *this,int param_1,int param_2)

{
                    /* 0x1190  369  ?setMeasurementRange@ObsInpSpec@@QAEXHH@Z */
  *(int *)(this + 0x20) = param_1;
  *(int *)(this + 0x24) = param_2;
  return;
}

//===== 0x100011b0 =====

/* public: void __thiscall ObsInpSpec::measRange(int &,int &,int &)const  */

void __thiscall ObsInpSpec::measRange(ObsInpSpec *this,int *param_1,int *param_2,int *param_3)

{
                    /* 0x11b0  277  ?measRange@ObsInpSpec@@QBEXAAH00@Z */
  *param_1 = *(int *)(this + 0x20);
  *param_2 = *(int *)(this + 0x24);
  *param_3 = *(int *)(this + 0x4c);
  return;
}

//===== 0x100011e0 =====

/* public: void __thiscall ObsInpSpec::widthStats(float &,float &)const  */

void __thiscall ObsInpSpec::widthStats(ObsInpSpec *this,float *param_1,float *param_2)

{
                    /* 0x11e0  441  ?widthStats@ObsInpSpec@@QBEXAAM0@Z */
  *param_1 = *(float *)(this + 0x58);
  *param_2 = *(float *)(this + 0x5c);
  return;
}

//===== 0x10001210 =====

/* public: int __thiscall ObsInpSpec::spacing(void)const  */

int __thiscall ObsInpSpec::spacing(ObsInpSpec *this)

{
                    /* 0x1210  405  ?spacing@ObsInpSpec@@QBEHXZ */
  return *(int *)(this + 0x50);
}

//===== 0x10001230 =====

/* public: enum ObsInpSpec::RC_ACTION __thiscall ObsInpSpec::action(void)const  */

RC_ACTION __thiscall ObsInpSpec::action(ObsInpSpec *this)

{
                    /* 0x1230  64  ?action@ObsInpSpec@@QBE?AW4RC_ACTION@1@XZ */
  return *(RC_ACTION *)(this + 0x60);
}

//===== 0x10001250 =====

/* public: int __thiscall ObsInpSpec::changedBy(void)const  */

int __thiscall ObsInpSpec::changedBy(ObsInpSpec *this)

{
                    /* 0x1250  110  ?changedBy@ObsInpSpec@@QBEHXZ */
  return *(int *)(this + 0x54);
}

//===== 0x10001270 =====

/* public: int __thiscall ObsInpSpec::angle(int)const  */

int __thiscall ObsInpSpec::angle(ObsInpSpec *this,int param_1)

{
                    /* 0x1270  67  ?angle@ObsInpSpec@@QBEHH@Z */
  return *(int *)(this + param_1 * 0x18 + 0x7c);
}

//===== 0x10001290 =====

/* public: float __thiscall ObsInpSpec::xtalk(int,int)const  */

float __thiscall ObsInpSpec::xtalk(ObsInpSpec *this,int param_1,int param_2)

{
                    /* 0x1290  450  ?xtalk@ObsInpSpec@@QBEMHH@Z */
  return *(float *)(this + param_2 * 4 + param_1 * 0x18 + 0x68);
}

//===== 0x100012b0 =====

/* public: int __thiscall ObsInpSpec::cfzones(void)const  */

int __thiscall ObsInpSpec::cfzones(ObsInpSpec *this)

{
                    /* 0x12b0  109  ?cfzones@ObsInpSpec@@QBEHXZ */
  return *(int *)(this + 0xd0);
}

//===== 0x100012d0 =====

/* public: int __thiscall ObsInpSpec::cfbgn(int)const  */

int __thiscall ObsInpSpec::cfbgn(ObsInpSpec *this,int param_1)

{
                    /* 0x12d0  105  ?cfbgn@ObsInpSpec@@QBEHH@Z */
  return *(int *)(*(int *)(this + 0xd4) + param_1 * 8);
}

//===== 0x100012f0 =====

/* public: int __thiscall ObsInpSpec::cfend(int)const  */

int __thiscall ObsInpSpec::cfend(ObsInpSpec *this,int param_1)

{
                    /* 0x12f0  106  ?cfend@ObsInpSpec@@QBEHH@Z */
  return *(int *)(*(int *)(this + 0xd4) + 4 + param_1 * 8);
}

//===== 0x10001310 =====

/* public: int __thiscall ObsInpSpec::cfsignal(int,int)const  */

int __thiscall ObsInpSpec::cfsignal(ObsInpSpec *this,int param_1,int param_2)

{
                    /* 0x1310  108  ?cfsignal@ObsInpSpec@@QBEHHH@Z */
  return *(int *)(*(int *)(this + param_1 * 4 + 0xd8) + param_2 * 8);
}

//===== 0x10001330 =====

/* public: int __thiscall ObsInpSpec::cfnoise(int,int)const  */

int __thiscall ObsInpSpec::cfnoise(ObsInpSpec *this,int param_1,int param_2)

{
                    /* 0x1330  107  ?cfnoise@ObsInpSpec@@QBEHHH@Z */
  return *(int *)(*(int *)(this + param_1 * 4 + 0xd8) + 4 + param_2 * 8);
}

//===== 0x10001360 =====

/* public: int __thiscall Annotate::getNumCurrFix(void)const  */

int __thiscall Annotate::getNumCurrFix(Annotate *this)

{
                    /* 0x1360  197  ?getNumCurrFix@Annotate@@QBEHXZ
                       0x1360  235  ?iS1@RdrOut@@QBEHXZ
                       0x1360  304  ?posn@BandStat@@QBEHXZ
                       0x1360  415  ?start@SSNODE@@QBEHXZ */
  return *(int *)(this + 4);
}

//===== 0x10001380 =====

/* public: void __thiscall Annotate::getCurrFix(int,long &,long &,int &,int &)const  */

void __thiscall
Annotate::getCurrFix
          (Annotate *this,int param_1,long *param_2,long *param_3,int *param_4,int *param_5)

{
                    /* 0x1380  182  ?getCurrFix@Annotate@@QBEXHAAJ0AAH1@Z */
  if ((-1 < param_1) && (param_1 < *(int *)(this + 4))) {
    *param_2 = *(long *)(*(int *)(this + 0xc) + param_1 * 0x10);
    *param_3 = *(long *)(*(int *)(this + 0xc) + 4 + param_1 * 0x10);
    *param_4 = *(int *)(*(int *)(this + 0xc) + 8 + param_1 * 0x10);
    *param_5 = *(int *)(*(int *)(this + 0xc) + 0xc + param_1 * 0x10);
  }
  return;
}

//===== 0x10001400 =====

/* public: void __thiscall Annotate::getMtrxDim(long &,long &)const  */

void __thiscall Annotate::getMtrxDim(Annotate *this,long *param_1,long *param_2)

{
                    /* 0x1400  194  ?getMtrxDim@Annotate@@QBEXAAJ0@Z */
  *param_1 = *(long *)(this + 0x28);
  *param_2 = *(long *)(this + 0x2c);
  return;
}

//===== 0x10001430 =====

/* public: double * * __thiscall Annotate::getTrace(enum Annotate::TraceId)const  */

double ** __thiscall Annotate::getTrace(Annotate *this,TraceId param_1)

{
  double **ppdVar1;
  
                    /* 0x1430  223  ?getTrace@Annotate@@QBEPAPANW4TraceId@1@@Z */
  if ((((int)param_1 < 0) || (3 < (int)param_1)) || (*(int *)(this + param_1 * 4 + 0x30) == 0)) {
    ppdVar1 = (double **)0x0;
  }
  else {
    ppdVar1 = *(double ***)(this + param_1 * 4 + 0x30);
  }
  return ppdVar1;
}

//===== 0x10001470 =====

/* public: float const * __thiscall Annotate::getCurrent(void)const  */

float * __thiscall Annotate::getCurrent(Annotate *this)

{
                    /* 0x1470  183  ?getCurrent@Annotate@@QBEPBMXZ */
  return *(float **)(this + 0x40);
}

//===== 0x10001490 =====

/* public: void __thiscall Annotate::getFwhmGapBp(int,float &,int &,int &)const  */

void __thiscall
Annotate::getFwhmGapBp(Annotate *this,int param_1,float *param_2,int *param_3,int *param_4)

{
                    /* 0x1490  186  ?getFwhmGapBp@Annotate@@QBEXHAAMAAH1@Z */
  if (((*(int *)(this + 0x14) != 0) && (-1 < param_1)) && (param_1 < *(int *)(this + 0x10))) {
    *param_2 = *(float *)(*(int *)(this + 0x14) + param_1 * 0xc);
    *param_3 = *(int *)(*(int *)(this + 0x14) + 4 + param_1 * 0xc);
    *param_4 = *(int *)(*(int *)(this + 0x14) + 8 + param_1 * 0xc);
  }
  return;
}

//===== 0x10001500 =====

/* public: int __thiscall Annotate::getCFlen(void)const  */

int __thiscall Annotate::getCFlen(Annotate *this)

{
                    /* 0x1500  180  ?getCFlen@Annotate@@QBEHXZ */
  return *(int *)(this + 0x18);
}

//===== 0x10001520 =====

/* public: class BandStatArray & __thiscall RdrOut::bandstat(void) */

BandStatArray * __thiscall RdrOut::bandstat(RdrOut *this)

{
                    /* 0x1520  79  ?bandstat@RdrOut@@QAEAAVBandStatArray@@XZ
                       0x1520  80  ?bandstat@RdrOut@@QBEABVBandStatArray@@XZ
                       0x1520  178  ?getCFOrdr@Annotate@@QBEPBDXZ */
  return (BandStatArray *)(this + 0x1c);
}

//===== 0x10001540 =====

/* public: int __thiscall Annotate::getSpecSepDepth(void)const  */

int __thiscall Annotate::getSpecSepDepth(Annotate *this)

{
                    /* 0x1540  217  ?getSpecSepDepth@Annotate@@QBEHXZ */
  return *(int *)(this + 0x44);
}

//===== 0x10001560 =====

/* public: void __thiscall Annotate::getNScnl(enum Annotate::TAxisChg,int &)const  */

void __thiscall Annotate::getNScnl(Annotate *this,TAxisChg param_1,int *param_2)

{
  int local_c;
  
                    /* 0x1560  195  ?getNScnl@Annotate@@QBEXW4TAxisChg@1@AAH@Z */
  if (((int)param_1 < 0) || (7 < (int)param_1)) {
    local_c = 0;
  }
  else {
    local_c = *(int *)(this + param_1 * 4 + 0x84);
  }
  *param_2 = local_c;
  return;
}

//===== 0x100015a0 =====

/* public: int __thiscall Annotate::getPsdSz(void)const  */

int __thiscall Annotate::getPsdSz(Annotate *this)

{
                    /* 0x15a0  205  ?getPsdSz@Annotate@@QBEHXZ */
  return *(int *)(this + 0x5c);
}

//===== 0x100015c0 =====

/* public: double * const * __thiscall Annotate::getPsd1(int &)const  */

double ** __thiscall Annotate::getPsd1(Annotate *this,int *param_1)

{
                    /* 0x15c0  203  ?getPsd1@Annotate@@QBEPBQANAAH@Z */
  *param_1 = *(int *)(this + 0x5c) / 2 + 1;
  return *(double ***)(this + 0x60);
}

//===== 0x100015f0 =====

/* public: double * const * __thiscall Annotate::getPsd2(int &)const  */

double ** __thiscall Annotate::getPsd2(Annotate *this,int *param_1)

{
                    /* 0x15f0  204  ?getPsd2@Annotate@@QBEPBQANAAH@Z */
  *param_1 = *(int *)(this + 0x5c) / 2 + 1;
  return *(double ***)(this + 100);
}

//===== 0x10001620 =====

/* public: void __thiscall Annotate::getDecimData(int &,int &,int &,float &,float &)const  */

void __thiscall
Annotate::getDecimData
          (Annotate *this,int *param_1,int *param_2,int *param_3,float *param_4,float *param_5)

{
                    /* 0x1620  184  ?getDecimData@Annotate@@QBEXAAH00AAM1@Z */
  *param_1 = *(int *)(this + 0x68);
  *param_2 = *(int *)(this + 0x6c);
  *param_3 = *(int *)(this + 0x70);
  *param_4 = *(float *)(this + 0x7c);
  *param_5 = *(float *)(this + 0x80);
  return;
}

//===== 0x10001670 =====

/* public: int __thiscall Annotate::getMobTblLen(void)const  */

int __thiscall Annotate::getMobTblLen(Annotate *this)

{
                    /* 0x1670  193  ?getMobTblLen@Annotate@@QBEHXZ */
  return *(int *)(this + 0xa4);
}

//===== 0x10001690 =====

/* public: void __thiscall Annotate::setSpecSepDepth(int) */

void __thiscall Annotate::setSpecSepDepth(Annotate *this,int param_1)

{
                    /* 0x1690  377  ?setSpecSepDepth@Annotate@@QAEXH@Z */
  *(int *)(this + 0x44) = param_1;
  return;
}

//===== 0x100016b0 =====

/* public: void __thiscall Annotate::setPsd1(double * *) */

void __thiscall Annotate::setPsd1(Annotate *this,double **param_1)

{
                    /* 0x16b0  373  ?setPsd1@Annotate@@QAEXPAPAN@Z */
  *(double ***)(this + 0x60) = param_1;
  return;
}

//===== 0x100016d0 =====

/* public: void __thiscall Annotate::setPsd2(double * *) */

void __thiscall Annotate::setPsd2(Annotate *this,double **param_1)

{
                    /* 0x16d0  374  ?setPsd2@Annotate@@QAEXPAPAN@Z */
  *(double ***)(this + 100) = param_1;
  return;
}

//===== 0x100016f0 =====

/* public: void __thiscall Annotate::setNScnl(enum Annotate::TAxisChg,int) */

void __thiscall Annotate::setNScnl(Annotate *this,TAxisChg param_1,int param_2)

{
                    /* 0x16f0  372  ?setNScnl@Annotate@@QAEXW4TAxisChg@1@H@Z */
  if ((-1 < (int)param_1) && ((int)param_1 < 8)) {
    *(int *)(this + param_1 * 4 + 0x84) = param_2;
  }
  return;
}

//===== 0x10001720 =====

/* public: void __thiscall Annotate::setCFOrdr(char const *) */

void __thiscall Annotate::setCFOrdr(Annotate *this,char *param_1)

{
  int local_8;
  
                    /* 0x1720  357  ?setCFOrdr@Annotate@@QAEXPBD@Z */
  for (local_8 = 0; local_8 < 6; local_8 = local_8 + 1) {
    this[local_8 + 0x1c] = *(Annotate *)(param_1 + local_8);
  }
  return;
}

//===== 0x10001760 =====

/* public: void __thiscall Annotate::setDecimData(int,int,int,float,float) */

void __thiscall
Annotate::setDecimData
          (Annotate *this,int param_1,int param_2,int param_3,float param_4,float param_5)

{
                    /* 0x1760  366  ?setDecimData@Annotate@@QAEXHHHMM@Z */
  *(int *)(this + 0x68) = param_1;
  *(int *)(this + 0x6c) = param_2;
  *(int *)(this + 0x70) = param_3;
  *(float *)(this + 0x7c) = param_4;
  *(float *)(this + 0x80) = param_5;
  return;
}

//===== 0x100017a0 =====

/* public: void __thiscall Wvfm::ds(enum Wvfm::DATASRC) */

void __thiscall Wvfm::ds(Wvfm *this,DATASRC param_1)

{
                    /* 0x17a0  146  ?ds@Wvfm@@QAEXW4DATASRC@1@@Z */
  *(DATASRC *)(this + 0xc0) = param_1;
  return;
}

//===== 0x100017c0 =====

/* public: void __thiscall Wvfm::smplRate(enum Wvfm::INTERPOLATE_BY) */

void __thiscall Wvfm::smplRate(Wvfm *this,INTERPOLATE_BY param_1)

{
                    /* 0x17c0  398  ?smplRate@Wvfm@@QAEXW4INTERPOLATE_BY@1@@Z */
  *(INTERPOLATE_BY *)(this + 0x16c) = param_1;
  return;
}

//===== 0x100017e0 =====

/* public: void __thiscall Wvfm::rows(int) */

void __thiscall Wvfm::rows(Wvfm *this,int param_1)

{
                    /* 0x17e0  342  ?rows@Wvfm@@QAEXH@Z */
  *(int *)(this + 0xb0) = param_1;
  return;
}

//===== 0x10001800 =====

/* public: void __thiscall Wvfm::cols(int) */

void __thiscall Wvfm::cols(Wvfm *this,int param_1)

{
                    /* 0x1800  113  ?cols@Wvfm@@QAEXH@Z */
  *(int *)(this + 0xb4) = param_1;
  return;
}

//===== 0x10001820 =====

/* public: void __thiscall Wvfm::bgni(int) */

void __thiscall Wvfm::bgni(Wvfm *this,int param_1)

{
                    /* 0x1820  91  ?bgni@Wvfm@@QAEXH@Z */
  *(int *)(this + 0xb8) = param_1;
  return;
}

//===== 0x10001840 =====

/* public: void __thiscall Wvfm::endi(int) */

void __thiscall Wvfm::endi(Wvfm *this,int param_1)

{
                    /* 0x1840  149  ?endi@Wvfm@@QAEXH@Z */
  *(int *)(this + 0xbc) = param_1;
  return;
}

//===== 0x10001860 =====

/* public: void __thiscall Wvfm::sc_la_set(int,int,double) */

void __thiscall Wvfm::sc_la_set(Wvfm *this,int param_1,int param_2,double param_3)

{
  int iVar1;
  
                    /* 0x1860  348  ?sc_la_set@Wvfm@@QAEXHHN@Z */
  iVar1 = *(int *)(*(int *)(this + 0xc4) + param_1 * 4);
  *(undefined4 *)(iVar1 + param_2 * 8) = param_3._0_4_;
  *(undefined4 *)(iVar1 + 4 + param_2 * 8) = param_3._4_4_;
  return;
}

//===== 0x10001890 =====

/* public: void __thiscall Wvfm::sc_la_mul(int,int,double) */

void __thiscall Wvfm::sc_la_mul(Wvfm *this,int param_1,int param_2,double param_3)

{
                    /* 0x1890  347  ?sc_la_mul@Wvfm@@QAEXHHN@Z */
  *(double *)(*(int *)(*(int *)(this + 0xc4) + param_1 * 4) + param_2 * 8) =
       *(double *)(*(int *)(*(int *)(this + 0xc4) + param_1 * 4) + param_2 * 8) * param_3;
  return;
}

//===== 0x100018d0 =====

/* public: void __thiscall Wvfm::ispec(class ObsInpSpec const &) */

void __thiscall Wvfm::ispec(Wvfm *this,ObsInpSpec *param_1)

{
                    /* 0x18d0  245  ?ispec@Wvfm@@QAEXABVObsInpSpec@@@Z */
  ObsInpSpec::operator=((ObsInpSpec *)(this + 0x210),param_1);
  return;
}

//===== 0x100018f0 =====

/* public: void __thiscall Wvfm::setCurr(int,float) */

void __thiscall Wvfm::setCurr(Wvfm *this,int param_1,float param_2)

{
                    /* 0x18f0  363  ?setCurr@Wvfm@@QAEXHM@Z */
  if (*(int *)(this + 0x300) != 0) {
    *(float *)(*(int *)(this + 0x300) + param_1 * 4) = param_2;
  }
  return;
}

//===== 0x10001920 =====

/* public: int __thiscall Wvfm::rows(void)const  */

int __thiscall Wvfm::rows(Wvfm *this)

{
                    /* 0x1920  343  ?rows@Wvfm@@QBEHXZ
                       0x1920  350  ?scanl@Wvfm@@QBEHXZ */
  return *(int *)(this + 0xb0);
}

//===== 0x10001940 =====

/* public: enum Wvfm::INTERPOLATE_BY __thiscall Wvfm::smplRate(void)const  */

INTERPOLATE_BY __thiscall Wvfm::smplRate(Wvfm *this)

{
                    /* 0x1940  399  ?smplRate@Wvfm@@QBE?AW4INTERPOLATE_BY@1@XZ */
  return *(INTERPOLATE_BY *)(this + 0x16c);
}

//===== 0x10001960 =====

/* public: int __thiscall Wvfm::hasSSTPattern(void)const  */

int __thiscall Wvfm::hasSSTPattern(Wvfm *this)

{
                    /* 0x1960  226  ?hasSSTPattern@Wvfm@@QBEHXZ */
  return *(int *)(this + 0x1bc);
}

//===== 0x10001980 =====

/* public: struct SSTLUT const * __thiscall Wvfm::sstlut(void)const  */

SSTLUT * __thiscall Wvfm::sstlut(Wvfm *this)

{
                    /* 0x1980  413  ?sstlut@Wvfm@@QBEPBUSSTLUT@@XZ */
  return (SSTLUT *)(this + 0x1c0);
}

//===== 0x100019a0 =====

/* public: enum Wvfm::DATASRC __thiscall Wvfm::ds(void)const  */

DATASRC __thiscall Wvfm::ds(Wvfm *this)

{
                    /* 0x19a0  147  ?ds@Wvfm@@QBE?AW4DATASRC@1@XZ */
  return *(DATASRC *)(this + 0xc0);
}

//===== 0x100019c0 =====

/* public: double __thiscall Wvfm::sc_la(int,int)const  */

double __thiscall Wvfm::sc_la(Wvfm *this,int param_1,int param_2)

{
                    /* 0x19c0  346  ?sc_la@Wvfm@@QBENHH@Z */
  return *(double *)(*(int *)(*(int *)(this + 0xc4) + param_1 * 4) + param_2 * 8);
}

//===== 0x100019f0 =====

/* public: double const * __thiscall Wvfm::ssm(void)const  */

double * __thiscall Wvfm::ssm(Wvfm *this)

{
                    /* 0x19f0  412  ?ssm@Wvfm@@QBEPBNXZ */
  return (double *)(this + 0xe8);
}

//===== 0x10001a10 =====

/* public: int __thiscall Wvfm::cols(void)const  */

int __thiscall Wvfm::cols(Wvfm *this)

{
                    /* 0x1a10  114  ?cols@Wvfm@@QBEHXZ
                       0x1a10  256  ?lanes@Wvfm@@QBEHXZ */
  return *(int *)(this + 0xb4);
}

//===== 0x10001a30 =====

/* public: int __thiscall Wvfm::obgni(void)const  */

int __thiscall Wvfm::obgni(Wvfm *this)

{
                    /* 0x1a30  294  ?obgni@Wvfm@@QBEHXZ */
  return *(int *)(this + 0x174);
}

//===== 0x10001a50 =====

/* public: int __thiscall Wvfm::oendi(void)const  */

int __thiscall Wvfm::oendi(Wvfm *this)

{
                    /* 0x1a50  295  ?oendi@Wvfm@@QBEHXZ */
  return *(int *)(this + 0x178);
}

//===== 0x10001a70 =====

/* public: int __thiscall Wvfm::bgni(void)const  */

int __thiscall Wvfm::bgni(Wvfm *this)

{
                    /* 0x1a70  92  ?bgni@Wvfm@@QBEHXZ */
  return *(int *)(this + 0xb8);
}

//===== 0x10001a90 =====

/* public: int __thiscall Wvfm::endi(void)const  */

int __thiscall Wvfm::endi(Wvfm *this)

{
                    /* 0x1a90  150  ?endi@Wvfm@@QBEHXZ */
  return *(int *)(this + 0xbc);
}

//===== 0x10001ab0 =====

/* public: double __thiscall Wvfm::envv(unsigned int)const  */

double __thiscall Wvfm::envv(Wvfm *this,uint param_1)

{
  undefined4 local_10;
  undefined4 uStack_c;
  
                    /* 0x1ab0  153  ?envv@Wvfm@@QBENI@Z */
  if (*(int *)(this + 200) == 0) {
    local_10 = 0;
    uStack_c = 0;
  }
  else {
    local_10 = *(undefined4 *)(*(int *)(this + 200) + param_1 * 8);
    uStack_c = *(undefined4 *)(*(int *)(this + 200) + 4 + param_1 * 8);
  }
  return (double)CONCAT44(uStack_c,local_10);
}

//===== 0x10001b00 =====

/* public: int __thiscall Wvfm::envi(unsigned int)const  */

int __thiscall Wvfm::envi(Wvfm *this,uint param_1)

{
  int local_c;
  
                    /* 0x1b00  152  ?envi@Wvfm@@QBEHI@Z */
  if (*(int *)(this + 0xcc) == 0) {
    local_c = 0;
  }
  else {
    local_c = *(int *)(*(int *)(this + 0xcc) + param_1 * 4);
  }
  return local_c;
}

//===== 0x10001b40 =====

/* public: double __thiscall Wvfm::xbnd(unsigned int)const  */

double __thiscall Wvfm::xbnd(Wvfm *this,uint param_1)

{
  undefined4 local_10;
  undefined4 uStack_c;
  
                    /* 0x1b40  449  ?xbnd@Wvfm@@QBENI@Z */
  if (*(int *)(this + 0xd0) == 0) {
    local_10 = 0;
    uStack_c = 0;
  }
  else {
    local_10 = *(undefined4 *)(*(int *)(this + 0xd0) + param_1 * 8);
    uStack_c = *(undefined4 *)(*(int *)(this + 0xd0) + 4 + param_1 * 8);
  }
  return (double)CONCAT44(uStack_c,local_10);
}

//===== 0x10001b90 =====

/* public: float __thiscall Wvfm::buzz(unsigned int)const  */

float __thiscall Wvfm::buzz(Wvfm *this,uint param_1)

{
  float local_c;
  
                    /* 0x1b90  100  ?buzz@Wvfm@@QBEMI@Z */
  if (*(int *)(this + 0xd4) == 0) {
    local_c = 0.0;
  }
  else {
    local_c = *(float *)(*(int *)(this + 0xd4) + param_1 * 4);
  }
  return local_c;
}

//===== 0x10001bd0 =====

/* public: enum Wvfm::Method __thiscall Wvfm::method(void)const  */

Method __thiscall Wvfm::method(Wvfm *this)

{
                    /* 0x1bd0  279  ?method@Wvfm@@QBE?AW4Method@1@XZ */
  return *(Method *)(this + 0xd8);
}

//===== 0x10001bf0 =====

/* public: char const * __thiscall Wvfm::lnordr(void)const  */

char * __thiscall Wvfm::lnordr(Wvfm *this)

{
                    /* 0x1bf0  267  ?lnordr@Wvfm@@QBEPBDXZ */
  return (char *)(this + 0xdc);
}

//===== 0x10001c10 =====

/* public: class ObsInpSpec const & __thiscall Wvfm::ispec(void)const  */

ObsInpSpec * __thiscall Wvfm::ispec(Wvfm *this)

{
                    /* 0x1c10  246  ?ispec@Wvfm@@QBEABVObsInpSpec@@XZ */
  return (ObsInpSpec *)(this + 0x210);
}

//===== 0x10001c30 =====

/* public: float __thiscall Wvfm::getCurr(int)const  */

float __thiscall Wvfm::getCurr(Wvfm *this,int param_1)

{
  float local_c;
  
                    /* 0x1c30  181  ?getCurr@Wvfm@@QBEMH@Z */
  if (*(int *)(this + 0x300) == 0) {
    local_c = 0.0;
  }
  else {
    local_c = *(float *)(*(int *)(this + 0x300) + param_1 * 4);
  }
  return local_c;
}

//===== 0x10001c70 =====

/* public: class Annotate const * __thiscall Wvfm::getAnnotation(void)const  */

Annotate * __thiscall Wvfm::getAnnotation(Wvfm *this)

{
  Annotate *local_c;
  
                    /* 0x1c70  175  ?getAnnotation@Wvfm@@QBEPBVAnnotate@@XZ */
  if (*(int *)this == 0) {
    local_c = (Annotate *)0x0;
  }
  else {
    local_c = (Annotate *)(this + 4);
  }
  return local_c;
}

//===== 0x10001ca0 =====

/* public: double * * __thiscall Wvfm::pwvfm(void)const  */

double ** __thiscall Wvfm::pwvfm(Wvfm *this)

{
                    /* 0x1ca0  316  ?pwvfm@Wvfm@@QBEPAPANXZ */
  return *(double ***)(this + 0xc4);
}

//===== 0x10001cc0 =====

/* public: void __thiscall Wvfm::getRawBgnEndPts(int &,int &)const  */

void __thiscall Wvfm::getRawBgnEndPts(Wvfm *this,int *param_1,int *param_2)

{
                    /* 0x1cc0  208  ?getRawBgnEndPts@Wvfm@@QBEXAAH0@Z */
  *param_1 = *(int *)(this + 0x2f8);
  *param_2 = *(int *)(this + 0x2fc);
  return;
}

//===== 0x10001cf0 =====

/* public: enum Wvfm::Status __thiscall Wvfm::status(void)const  */

Status __thiscall Wvfm::status(Wvfm *this)

{
                    /* 0x1cf0  417  ?status@Wvfm@@QBE?AW4Status@1@XZ */
  return *(Status *)(this + 0x168);
}

//===== 0x10001d10 =====

/* public: void __thiscall Wvfm::resol(int &,int &)const  */

void __thiscall Wvfm::resol(Wvfm *this,int *param_1,int *param_2)

{
                    /* 0x1d10  341  ?resol@Wvfm@@QBEXAAH0@Z */
  *param_1 = *(int *)(this + 0x1b4);
  *param_2 = *(int *)(this + 0x1b8);
  return;
}

//===== 0x10001d40 =====

/* private: void __thiscall Wvfm::sc_la_sub(int,int,double)const  */

void __thiscall Wvfm::sc_la_sub(Wvfm *this,int param_1,int param_2,double param_3)

{
                    /* 0x1d40  349  ?sc_la_sub@Wvfm@@ABEXHHN@Z */
  *(double *)(*(int *)(*(int *)(this + 0xc4) + param_1 * 4) + param_2 * 8) =
       *(double *)(*(int *)(*(int *)(this + 0xc4) + param_1 * 4) + param_2 * 8) - param_3;
  return;
}

//===== 0x10001d80 =====

/* private: double * __thiscall Wvfm::operator[](int) */

double * __thiscall Wvfm::operator[](Wvfm *this,int param_1)

{
                    /* 0x1d80  56  ??AWvfm@@AAEPANH@Z */
  return *(double **)(*(int *)(this + 0xc4) + param_1 * 4);
}

//===== 0x10001da0 =====

/* public: void __thiscall Wvfm::annotate(int) */

void __thiscall Wvfm::annotate(Wvfm *this,int param_1)

{
                    /* 0x1da0  69  ?annotate@Wvfm@@QAEXH@Z
                       0x1da0  163  ?fltwid@SSNODE@@QAEXH@Z
                       0x1da0  289  ?ntnr@BandStat@@QAEXH@Z */
  *(int *)this = param_1;
  return;
}

//===== 0x10001dc0 =====

/* public: void __thiscall RdrOut::iS1(int) */

void __thiscall RdrOut::iS1(RdrOut *this,int param_1)

{
                    /* 0x1dc0  234  ?iS1@RdrOut@@QAEXH@Z
                       0x1dc0  303  ?posn@BandStat@@QAEXH@Z
                       0x1dc0  414  ?start@SSNODE@@QAEXH@Z */
  *(int *)(this + 4) = param_1;
  return;
}

//===== 0x10001de0 =====

/* public: void __thiscall BandStat::hght(float) */

void __thiscall BandStat::hght(BandStat *this,float param_1)

{
                    /* 0x1de0  228  ?hght@BandStat@@QAEXM@Z */
  *(float *)(this + 0x14) = param_1;
  return;
}

//===== 0x10001e00 =====

/* public: void __thiscall BandStat::lowv(float) */

void __thiscall BandStat::lowv(BandStat *this,float param_1)

{
                    /* 0x1e00  268  ?lowv@BandStat@@QAEXM@Z */
  *(float *)(this + 0x18) = param_1;
  return;
}

//===== 0x10001e20 =====

/* public: void __thiscall BandStat::xbnd(float) */

void __thiscall BandStat::xbnd(BandStat *this,float param_1)

{
                    /* 0x1e20  445  ?xbnd@BandStat@@QAEXM@Z */
  *(float *)(this + 0x1c) = param_1;
  return;
}

//===== 0x10001e40 =====

/* public: void __thiscall BandStat::shap(float) */

void __thiscall BandStat::shap(BandStat *this,float param_1)

{
                    /* 0x1e40  390  ?shap@BandStat@@QAEXM@Z */
  *(float *)(this + 0x20) = param_1;
  return;
}

//===== 0x10001e60 =====

/* public: void __thiscall ObsInpSpec::putativePks(int) */

void __thiscall ObsInpSpec::putativePks(ObsInpSpec *this,int param_1)

{
                    /* 0x1e60  315  ?putativePks@ObsInpSpec@@QAEXH@Z
                       0x1e60  436  ?widt@BandStat@@QAEXM@Z */
  *(int *)(this + 0x28) = param_1;
  return;
}

//===== 0x10001e80 =====

/* public: void __thiscall BandStat::lgap(float) */

void __thiscall BandStat::lgap(BandStat *this,float param_1)

{
                    /* 0x1e80  258  ?lgap@BandStat@@QAEXM@Z */
  *(float *)(this + 0x2c) = param_1;
  return;
}

//===== 0x10001ea0 =====

/* public: void __thiscall BandStat::sgap(float) */

void __thiscall BandStat::sgap(BandStat *this,float param_1)

{
                    /* 0x1ea0  386  ?sgap@BandStat@@QAEXM@Z */
  *(float *)(this + 0x30) = param_1;
  return;
}

//===== 0x10001ec0 =====

/* public: void __thiscall BandStat::buzz(float) */

void __thiscall BandStat::buzz(BandStat *this,float param_1)

{
                    /* 0x1ec0  96  ?buzz@BandStat@@QAEXM@Z */
  *(float *)(this + 0x24) = param_1;
  return;
}

//===== 0x10001ee0 =====

/* public: void __thiscall BandStat::call(char) */

void __thiscall BandStat::call(BandStat *this,char param_1)

{
                    /* 0x1ee0  101  ?call@BandStat@@QAEXD@Z */
  this[0x34] = (BandStat)param_1;
  return;
}

//===== 0x10001f00 =====

/* public: void __thiscall BandStat::iubc(char) */

void __thiscall BandStat::iubc(BandStat *this,char param_1)

{
                    /* 0x1f00  247  ?iubc@BandStat@@QAEXD@Z */
  this[0x35] = (BandStat)param_1;
  return;
}

//===== 0x10001f20 =====

/* public: void __thiscall BandStat::qual(float) */

void __thiscall BandStat::qual(BandStat *this,float param_1)

{
                    /* 0x1f20  318  ?qual@BandStat@@QAEXM@Z */
  *(float *)(this + 0x38) = param_1;
  return;
}

//===== 0x10001f40 =====

/* public: void __thiscall BandStat::snr(float) */

void __thiscall BandStat::snr(BandStat *this,float param_1)

{
                    /* 0x1f40  400  ?snr@BandStat@@QAEXM@Z */
  *(float *)(this + 0x3c) = param_1;
  return;
}

//===== 0x10001f60 =====

/* public: void __thiscall BandStat::squad(float * const) */

void __thiscall BandStat::squad(BandStat *this,float *param_1)

{
                    /* 0x1f60  409  ?squad@BandStat@@QAEXQAM@Z */
  *(float *)(this + 0x40) = *param_1;
  *(float *)(this + 0x44) = param_1[1];
  *(float *)(this + 0x48) = param_1[2];
  *(float *)(this + 0x4c) = param_1[3];
  return;
}

//===== 0x10001fa0 =====

/* public: float __thiscall BandStat::hght(void)const  */

float __thiscall BandStat::hght(BandStat *this)

{
                    /* 0x1fa0  229  ?hght@BandStat@@QBEMXZ */
  return *(float *)(this + 0x14);
}

//===== 0x10001fc0 =====

/* public: float __thiscall BandStat::lowv(void)const  */

float __thiscall BandStat::lowv(BandStat *this)

{
                    /* 0x1fc0  269  ?lowv@BandStat@@QBEMXZ */
  return *(float *)(this + 0x18);
}

//===== 0x10001fe0 =====

/* public: float __thiscall BandStat::xbnd(void)const  */

float __thiscall BandStat::xbnd(BandStat *this)

{
                    /* 0x1fe0  446  ?xbnd@BandStat@@QBEMXZ */
  return *(float *)(this + 0x1c);
}

//===== 0x10002000 =====

/* public: float __thiscall BandStat::shap(void)const  */

float __thiscall BandStat::shap(BandStat *this)

{
                    /* 0x2000  391  ?shap@BandStat@@QBEMXZ */
  return *(float *)(this + 0x20);
}

//===== 0x10002020 =====

/* public: float __thiscall BandStat::widt(void)const  */

float __thiscall BandStat::widt(BandStat *this)

{
                    /* 0x2020  437  ?widt@BandStat@@QBEMXZ */
  return *(float *)(this + 0x28);
}

//===== 0x10002040 =====

/* public: float __thiscall BandStat::lgap(void)const  */

float __thiscall BandStat::lgap(BandStat *this)

{
                    /* 0x2040  259  ?lgap@BandStat@@QBEMXZ */
  return *(float *)(this + 0x2c);
}

//===== 0x10002060 =====

/* public: float __thiscall BandStat::sgap(void)const  */

float __thiscall BandStat::sgap(BandStat *this)

{
                    /* 0x2060  387  ?sgap@BandStat@@QBEMXZ */
  return *(float *)(this + 0x30);
}

//===== 0x10002080 =====

/* public: float __thiscall BandStat::buzz(void)const  */

float __thiscall BandStat::buzz(BandStat *this)

{
                    /* 0x2080  97  ?buzz@BandStat@@QBEMXZ */
  return *(float *)(this + 0x24);
}

//===== 0x100020a0 =====

/* public: int __thiscall BandStat::awid(void)const  */

int __thiscall BandStat::awid(BandStat *this)

{
                    /* 0x20a0  75  ?awid@BandStat@@QBEHXZ */
  return (*(int *)(this + 0xc) - *(int *)(this + 8)) + 1;
}

//===== 0x100020c0 =====

/* public: float __thiscall BandStat::qual(void)const  */

float __thiscall BandStat::qual(BandStat *this)

{
                    /* 0x20c0  319  ?qual@BandStat@@QBEMXZ */
  return *(float *)(this + 0x38);
}

//===== 0x100020e0 =====

/* public: float __thiscall BandStat::snr(void)const  */

float __thiscall BandStat::snr(BandStat *this)

{
                    /* 0x20e0  401  ?snr@BandStat@@QBEMXZ */
  return *(float *)(this + 0x3c);
}

//===== 0x10002100 =====

/* public: void __thiscall BandStat::gquad(float * const)const  */

void __thiscall BandStat::gquad(BandStat *this,float *param_1)

{
                    /* 0x2100  225  ?gquad@BandStat@@QBEXQAM@Z */
  *param_1 = *(float *)(this + 0x40);
  param_1[1] = *(float *)(this + 0x44);
  param_1[2] = *(float *)(this + 0x48);
  param_1[3] = *(float *)(this + 0x4c);
  return;
}

//===== 0x10002140 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: float __thiscall BandStat::StadenQual(void)const  */

float __thiscall BandStat::StadenQual(BandStat *this)

{
                    /* 0x2140  62  ?StadenQual@BandStat@@QBEMXZ */
  return _DAT_100380ec * *(float *)(this + 0x38) + _DAT_100380f0;
}

//===== 0x10002160 =====

/* public: char __thiscall BandStat::call(void)const  */

char __thiscall BandStat::call(BandStat *this)

{
                    /* 0x2160  102  ?call@BandStat@@QBEDXZ */
  return (char)this[0x34];
}

//===== 0x10002180 =====

/* public: char __thiscall BandStat::iubc(void)const  */

char __thiscall BandStat::iubc(BandStat *this)

{
                    /* 0x2180  248  ?iubc@BandStat@@QBEDXZ */
  return (char)this[0x35];
}

//===== 0x100021a0 =====

/* public: class BandStat & __thiscall BandStat::operator=(class BandStat const &) */

BandStat * __thiscall BandStat::operator=(BandStat *this,BandStat *param_1)

{
  int iVar1;
  BandStat *pBVar2;
  
  pBVar2 = this;
                    /* 0x21a0  44  ??4BandStat@@QAEAAV0@ABV0@@Z */
  for (iVar1 = 0x14; iVar1 != 0; iVar1 = iVar1 + -1) {
    *(undefined4 *)pBVar2 = *(undefined4 *)param_1;
    param_1 = param_1 + 4;
    pBVar2 = pBVar2 + 4;
  }
  return this;
}

//===== 0x100021d0 =====

/* public: void __thiscall BandStatArray::declen(void) */

void __thiscall BandStatArray::declen(BandStatArray *this)

{
                    /* 0x21d0  136  ?declen@BandStatArray@@QAEXXZ */
  *(int *)this = *(int *)this + -1;
  return;
}

//===== 0x100021f0 =====

/* public: void __thiscall BandStatArray::ntnr(int,int) */

void __thiscall BandStatArray::ntnr(BandStatArray *this,int param_1,int param_2)

{
                    /* 0x21f0  291  ?ntnr@BandStatArray@@QAEXHH@Z */
  Wvfm::annotate((Wvfm *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002220 =====

/* public: void __thiscall BandStatArray::posn(int,int) */

void __thiscall BandStatArray::posn(BandStatArray *this,int param_1,int param_2)

{
                    /* 0x2220  305  ?posn@BandStatArray@@QAEXHH@Z */
  RdrOut::iS1((RdrOut *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002250 =====

/* public: void __thiscall BandStatArray::bbgn(int,int) */

void __thiscall BandStatArray::bbgn(BandStatArray *this,int param_1,int param_2)

{
                    /* 0x2250  83  ?bbgn@BandStatArray@@QAEXHH@Z */
  BandStat::bbgn((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002280 =====

/* public: void __thiscall BandStatArray::bend(int,int) */

void __thiscall BandStatArray::bend(BandStatArray *this,int param_1,int param_2)

{
                    /* 0x2280  87  ?bend@BandStatArray@@QAEXHH@Z */
  SSNODE::SWold((SSNODE *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x100022b0 =====

/* public: void __thiscall BandStatArray::insr(int,int) */

void __thiscall BandStatArray::insr(BandStatArray *this,int param_1,int param_2)

{
                    /* 0x22b0  242  ?insr@BandStatArray@@QAEXHH@Z */
  BandStat::insr((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x100022e0 =====

/* public: void __thiscall BandStatArray::hght(int,float) */

void __thiscall BandStatArray::hght(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x22e0  230  ?hght@BandStatArray@@QAEXHM@Z */
  BandStat::hght((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002310 =====

/* public: void __thiscall BandStatArray::lowv(int,float) */

void __thiscall BandStatArray::lowv(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x2310  270  ?lowv@BandStatArray@@QAEXHM@Z */
  BandStat::lowv((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002340 =====

/* public: void __thiscall BandStatArray::xbnd(int,float) */

void __thiscall BandStatArray::xbnd(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x2340  447  ?xbnd@BandStatArray@@QAEXHM@Z */
  BandStat::xbnd((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002370 =====

/* public: void __thiscall BandStatArray::shap(int,float) */

void __thiscall BandStatArray::shap(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x2370  392  ?shap@BandStatArray@@QAEXHM@Z */
  BandStat::shap((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x100023a0 =====

/* public: void __thiscall BandStatArray::buzz(int,float) */

void __thiscall BandStatArray::buzz(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x23a0  98  ?buzz@BandStatArray@@QAEXHM@Z */
  BandStat::buzz((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x100023d0 =====

/* public: void __thiscall BandStatArray::widt(int,float) */

void __thiscall BandStatArray::widt(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x23d0  438  ?widt@BandStatArray@@QAEXHM@Z */
  ObsInpSpec::putativePks((ObsInpSpec *)(param_1 * 0x50 + *(int *)(this + 4)),(int)param_2);
  return;
}

//===== 0x10002400 =====

/* public: void __thiscall BandStatArray::lgap(int,float) */

void __thiscall BandStatArray::lgap(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x2400  260  ?lgap@BandStatArray@@QAEXHM@Z */
  BandStat::lgap((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002430 =====

/* public: void __thiscall BandStatArray::sgap(int,float) */

void __thiscall BandStatArray::sgap(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x2430  388  ?sgap@BandStatArray@@QAEXHM@Z */
  BandStat::sgap((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002460 =====

/* public: void __thiscall BandStatArray::qual(int,float) */

void __thiscall BandStatArray::qual(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x2460  320  ?qual@BandStatArray@@QAEXHM@Z */
  BandStat::qual((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002490 =====

/* public: void __thiscall BandStatArray::call(int,char) */

void __thiscall BandStatArray::call(BandStatArray *this,int param_1,char param_2)

{
                    /* 0x2490  103  ?call@BandStatArray@@QAEXHD@Z */
  BandStat::call((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x100024c0 =====

/* public: void __thiscall BandStatArray::iubc(int,char) */

void __thiscall BandStatArray::iubc(BandStatArray *this,int param_1,char param_2)

{
                    /* 0x24c0  249  ?iubc@BandStatArray@@QAEXHD@Z */
  BandStat::iubc((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x100024f0 =====

/* public: void __thiscall BandStatArray::squad(int,float * const) */

void __thiscall BandStatArray::squad(BandStatArray *this,int param_1,float *param_2)

{
                    /* 0x24f0  410  ?squad@BandStatArray@@QAEXHQAM@Z */
  BandStat::squad((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002520 =====

/* public: void __thiscall BandStatArray::snr(int,float) */

void __thiscall BandStatArray::snr(BandStatArray *this,int param_1,float param_2)

{
                    /* 0x2520  402  ?snr@BandStatArray@@QAEXHM@Z */
  BandStat::snr((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x10002550 =====

/* public: int __thiscall BandStatArray::ntnr(int)const  */

int __thiscall BandStatArray::ntnr(BandStatArray *this,int param_1)

{
  int iVar1;
  
                    /* 0x2550  292  ?ntnr@BandStatArray@@QBEHH@Z */
  iVar1 = Wvfm::annotate((Wvfm *)(*(int *)(this + 4) + param_1 * 0x50));
  return iVar1;
}

//===== 0x10002570 =====

/* public: int __thiscall BandStatArray::posn(int)const  */

int __thiscall BandStatArray::posn(BandStatArray *this,int param_1)

{
  int iVar1;
  
                    /* 0x2570  306  ?posn@BandStatArray@@QBEHH@Z */
  iVar1 = Annotate::getNumCurrFix((Annotate *)(*(int *)(this + 4) + param_1 * 0x50));
  return iVar1;
}

//===== 0x10002590 =====

/* public: int __thiscall BandStatArray::bbgn(int)const  */

int __thiscall BandStatArray::bbgn(BandStatArray *this,int param_1)

{
  int iVar1;
  
                    /* 0x2590  84  ?bbgn@BandStatArray@@QBEHH@Z */
  iVar1 = SW::alignedLength((SW *)(*(int *)(this + 4) + param_1 * 0x50));
  return iVar1;
}

//===== 0x100025b0 =====

/* public: int __thiscall BandStatArray::bend(int)const  */

int __thiscall BandStatArray::bend(BandStatArray *this,int param_1)

{
  int iVar1;
  
                    /* 0x25b0  88  ?bend@BandStatArray@@QBEHH@Z */
  iVar1 = SSNODE::SWold((SSNODE *)(*(int *)(this + 4) + param_1 * 0x50));
  return iVar1;
}

//===== 0x100025d0 =====

/* public: int __thiscall BandStatArray::insr(int)const  */

int __thiscall BandStatArray::insr(BandStatArray *this,int param_1)

{
  int iVar1;
  
                    /* 0x25d0  243  ?insr@BandStatArray@@QBEHH@Z */
  iVar1 = Annotate::getNumFwhmGapLen((Annotate *)(*(int *)(this + 4) + param_1 * 0x50));
  return iVar1;
}

//===== 0x100025f0 =====

/* public: float __thiscall BandStatArray::hght(int)const  */

float __thiscall BandStatArray::hght(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x25f0  231  ?hght@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::hght((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x10002610 =====

/* public: float __thiscall BandStatArray::lowv(int)const  */

float __thiscall BandStatArray::lowv(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x2610  271  ?lowv@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::lowv((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x10002630 =====

/* public: float __thiscall BandStatArray::xbnd(int)const  */

float __thiscall BandStatArray::xbnd(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x2630  448  ?xbnd@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::xbnd((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x10002650 =====

/* public: float __thiscall BandStatArray::shap(int)const  */

float __thiscall BandStatArray::shap(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x2650  393  ?shap@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::shap((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x10002670 =====

/* public: float __thiscall BandStatArray::buzz(int)const  */

float __thiscall BandStatArray::buzz(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x2670  99  ?buzz@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::buzz((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x10002690 =====

/* public: float __thiscall BandStatArray::widt(int)const  */

float __thiscall BandStatArray::widt(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x2690  439  ?widt@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::widt((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x100026b0 =====

/* public: float __thiscall BandStatArray::lgap(int)const  */

float __thiscall BandStatArray::lgap(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x26b0  261  ?lgap@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::lgap((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x100026d0 =====

/* public: float __thiscall BandStatArray::sgap(int)const  */

float __thiscall BandStatArray::sgap(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x26d0  389  ?sgap@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::sgap((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x100026f0 =====

/* public: float __thiscall BandStatArray::qual(int)const  */

float __thiscall BandStatArray::qual(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x26f0  321  ?qual@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::qual((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x10002710 =====

/* public: float __thiscall BandStatArray::StadenQual(int)const  */

float __thiscall BandStatArray::StadenQual(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x2710  63  ?StadenQual@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::StadenQual((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x10002730 =====

/* public: char __thiscall BandStatArray::call(int)const  */

char __thiscall BandStatArray::call(BandStatArray *this,int param_1)

{
  char cVar1;
  
                    /* 0x2730  104  ?call@BandStatArray@@QBEDH@Z */
  cVar1 = BandStat::call((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return cVar1;
}

//===== 0x10002750 =====

/* public: char __thiscall BandStatArray::iubc(int)const  */

char __thiscall BandStatArray::iubc(BandStatArray *this,int param_1)

{
  char cVar1;
  
                    /* 0x2750  250  ?iubc@BandStatArray@@QBEDH@Z */
  cVar1 = BandStat::iubc((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return cVar1;
}

//===== 0x10002770 =====

/* public: void __thiscall BandStatArray::quad(int,float * const)const  */

void __thiscall BandStatArray::quad(BandStatArray *this,int param_1,float *param_2)

{
                    /* 0x2770  317  ?quad@BandStatArray@@QBEXHQAM@Z */
  BandStat::gquad((BandStat *)(param_1 * 0x50 + *(int *)(this + 4)),param_2);
  return;
}

//===== 0x100027a0 =====

/* public: float __thiscall BandStatArray::snr(int)const  */

float __thiscall BandStatArray::snr(BandStatArray *this,int param_1)

{
  float fVar1;
  
                    /* 0x27a0  403  ?snr@BandStatArray@@QBEMH@Z */
  fVar1 = BandStat::snr((BandStat *)(*(int *)(this + 4) + param_1 * 0x50));
  return fVar1;
}

//===== 0x100027c0 =====

/* public: int __thiscall Wvfm::annotate(void)const  */

int __thiscall Wvfm::annotate(Wvfm *this)

{
                    /* 0x27c0  70  ?annotate@Wvfm@@QBEHXZ
                       0x27c0  164  ?fltwid@SSNODE@@QBEHXZ
                       0x27c0  257  ?len@BandStatArray@@QBEHXZ
                       0x27c0  290  ?ntnr@BandStat@@QBEHXZ */
  return *(int *)this;
}

//===== 0x100027d0 =====

/* public: class BandStat & __thiscall BandStatArray::band(int) */

BandStat * __thiscall BandStatArray::band(BandStatArray *this,int param_1)

{
                    /* 0x27d0  76  ?band@BandStatArray@@QAEAAVBandStat@@H@Z
                       0x27d0  77  ?band@BandStatArray@@QBEABVBandStat@@H@Z */
  return (BandStat *)(param_1 * 0x50 + *(int *)(this + 4));
}

//===== 0x100027f0 =====

/* public: int __thiscall SSNODE::rdlen(void)const  */

int __thiscall SSNODE::rdlen(SSNODE *this)

{
                    /* 0x27f0  330  ?rdlen@SSNODE@@QBEHXZ */
  return (*(int *)(this + 8) - *(int *)(this + 4)) + 1;
}

//===== 0x10002810 =====

/* public: float __thiscall SSNODE::thresh(void)const  */

float __thiscall SSNODE::thresh(SSNODE *this)

{
                    /* 0x2810  425  ?thresh@SSNODE@@QBEMXZ */
  return *(float *)(this + 0x10);
}

//===== 0x10002830 =====

/* public: void __thiscall BandStat::bbgn(int) */

void __thiscall BandStat::bbgn(BandStat *this,int param_1)

{
                    /* 0x2830  81  ?bbgn@BandStat@@QAEXH@Z
                       0x2830  158  ?finish@SSNODE@@QAEXH@Z
                       0x2830  361  ?setCFixSts@Annotate@@QAEXH@Z */
  *(int *)(this + 8) = param_1;
  return;
}

//===== 0x10002850 =====

/* public: void __thiscall SSNODE::SWold(int) */

void __thiscall SSNODE::SWold(SSNODE *this,int param_1)

{
                    /* 0x2850  60  ?SWold@SSNODE@@QAEXH@Z
                       0x2850  85  ?bend@BandStat@@QAEXH@Z */
  *(int *)(this + 0xc) = param_1;
  return;
}

//===== 0x10002870 =====

/* public: void __thiscall BandStat::insr(int) */

void __thiscall BandStat::insr(BandStat *this,int param_1)

{
                    /* 0x2870  240  ?insr@BandStat@@QAEXH@Z
                       0x2870  424  ?thresh@SSNODE@@QAEXM@Z */
  *(int *)(this + 0x10) = param_1;
  return;
}

//===== 0x10002890 =====

/* public: class SSNODE & __thiscall SSNODE::operator=(class SSNODE const &) */

SSNODE * __thiscall SSNODE::operator=(SSNODE *this,SSNODE *param_1)

{
  int iVar1;
  SSNODE *pSVar2;
  
  pSVar2 = this;
                    /* 0x2890  52  ??4SSNODE@@QAEAAV0@ABV0@@Z */
  for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
    *(undefined4 *)pSVar2 = *(undefined4 *)param_1;
    param_1 = param_1 + 4;
    pSVar2 = pSVar2 + 4;
  }
  return this;
}

//===== 0x100028c0 =====

/* public: void __thiscall QualCtrl::shft(int,class ShftVect const &) */

void __thiscall QualCtrl::shft(QualCtrl *this,int param_1,ShftVect *param_2)

{
  undefined4 uVar1;
  
                    /* 0x28c0  394  ?shft@QualCtrl@@QAEXHABVShftVect@@@Z */
  if (param_1 < 0xc) {
    uVar1 = *(undefined4 *)(param_2 + 4);
    *(undefined4 *)(this + param_1 * 8) = *(undefined4 *)param_2;
    *(undefined4 *)(this + param_1 * 8 + 4) = uVar1;
  }
  return;
}

//===== 0x100028f0 =====

/* public: void __thiscall QualCtrl::fbw(int,int) */

void __thiscall QualCtrl::fbw(QualCtrl *this,int param_1,int param_2)

{
                    /* 0x28f0  156  ?fbw@QualCtrl@@QAEXHH@Z */
  if (param_1 < 0xc) {
    *(int *)(this + param_1 * 4 + 0x60) = param_2;
  }
  return;
}

//===== 0x10002910 =====

/* public: void __thiscall QualCtrl::bspac(int,int) */

void __thiscall QualCtrl::bspac(QualCtrl *this,int param_1,int param_2)

{
                    /* 0x2910  94  ?bspac@QualCtrl@@QAEXHH@Z */
  if (param_1 < 0xc) {
    *(int *)(this + param_1 * 4 + 0x90) = param_2;
  }
  return;
}

//===== 0x10002940 =====

/* public: void __thiscall QualCtrl::nseg(int) */

void __thiscall QualCtrl::nseg(QualCtrl *this,int param_1)

{
                    /* 0x2940  287  ?nseg@QualCtrl@@QAEXH@Z */
  *(int *)(this + 200) = param_1;
  return;
}

//===== 0x10002960 =====

/* public: void __thiscall QualCtrl::cutdata(class SSNODE const &) */

void __thiscall QualCtrl::cutdata(QualCtrl *this,SSNODE *param_1)

{
  int iVar1;
  QualCtrl *pQVar2;
  
                    /* 0x2960  120  ?cutdata@QualCtrl@@QAEXABVSSNODE@@@Z */
  pQVar2 = this + 0xcc;
  for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
    *(undefined4 *)pQVar2 = *(undefined4 *)param_1;
    param_1 = param_1 + 4;
    pQVar2 = pQVar2 + 4;
  }
  return;
}

//===== 0x10002990 =====

/* public: void __thiscall QualCtrl::startTimer(void) */

void __thiscall QualCtrl::startTimer(QualCtrl *this)

{
  time_t tVar1;
  
                    /* 0x2990  416  ?startTimer@QualCtrl@@QAEXXZ */
  tVar1 = time((time_t *)0x0);
  *(int *)(this + 0xc0) = (int)tVar1;
  return;
}

//===== 0x100029b0 =====

/* public: void __thiscall QualCtrl::stopTimer(void) */

void __thiscall QualCtrl::stopTimer(QualCtrl *this)

{
  time_t tVar1;
  
                    /* 0x29b0  418  ?stopTimer@QualCtrl@@QAEXXZ */
  tVar1 = time((time_t *)0x0);
  *(int *)(this + 0xc4) = (int)tVar1;
  return;
}

//===== 0x100029d0 =====

/* public: int __thiscall QualCtrl::nseg(void)const  */

int __thiscall QualCtrl::nseg(QualCtrl *this)

{
                    /* 0x29d0  288  ?nseg@QualCtrl@@QBEHXZ */
  return *(int *)(this + 200);
}

//===== 0x100029f0 =====

/* public: class SSNODE & __thiscall QualCtrl::cutdata(void) */

SSNODE * __thiscall QualCtrl::cutdata(QualCtrl *this)

{
                    /* 0x29f0  119  ?cutdata@QualCtrl@@QAEAAVSSNODE@@XZ
                       0x29f0  121  ?cutdata@QualCtrl@@QBEABVSSNODE@@XZ */
  return (SSNODE *)(this + 0xcc);
}

//===== 0x10002a10 =====

/* public: char const * __thiscall QualCtrl::ignoredSeq(void)const  */

char * __thiscall QualCtrl::ignoredSeq(QualCtrl *this)

{
                    /* 0x2a10  236  ?ignoredSeq@QualCtrl@@QBEPBDXZ */
  return (char *)0x0;
}

//===== 0x10002a20 =====

/* public: class ShftVect __thiscall QualCtrl::shft(int)const  */

int __thiscall QualCtrl::shft(QualCtrl *this,int param_1)

{
  undefined4 uVar1;
  int iVar2;
  int in_stack_00000008;
  QualCtrl *local_10;
  
                    /* 0x2a20  395  ?shft@QualCtrl@@QBE?AVShftVect@@H@Z */
  iVar2 = nseg(this);
  local_10 = this;
  if (in_stack_00000008 < iVar2) {
    local_10 = this + in_stack_00000008 * 8;
  }
  uVar1 = *(undefined4 *)(local_10 + 4);
  *(undefined4 *)param_1 = *(undefined4 *)local_10;
  *(undefined4 *)(param_1 + 4) = uVar1;
  return param_1;
}

//===== 0x10002a70 =====

/* public: int __thiscall QualCtrl::fbw(int)const  */

int __thiscall QualCtrl::fbw(QualCtrl *this,int param_1)

{
  int local_c;
  
                    /* 0x2a70  157  ?fbw@QualCtrl@@QBEHH@Z */
  if (param_1 < 0xc) {
    local_c = *(int *)(this + param_1 * 4 + 0x60);
  }
  else {
    local_c = -1;
  }
  return local_c;
}

//===== 0x10002aa0 =====

/* public: int __thiscall QualCtrl::bspac(int)const  */

int __thiscall QualCtrl::bspac(QualCtrl *this,int param_1)

{
  int local_c;
  
                    /* 0x2aa0  95  ?bspac@QualCtrl@@QBEHH@Z */
  if (param_1 < 0xc) {
    local_c = *(int *)(this + param_1 * 4 + 0x90);
  }
  else {
    local_c = -1;
  }
  return local_c;
}

//===== 0x10002ae0 =====

/* public: long __thiscall QualCtrl::runtime(void)const  */

long __thiscall QualCtrl::runtime(QualCtrl *this)

{
                    /* 0x2ae0  344  ?runtime@QualCtrl@@QBEJXZ */
  return (*(int *)(this + 0xc4) - *(int *)(this + 0xc0)) + 1;
}

//===== 0x10002b00 =====

/* public: class Wvfm & __thiscall RdrOut::wvfm(void) */

Wvfm * __thiscall RdrOut::wvfm(RdrOut *this)

{
                    /* 0x2b00  442  ?wvfm@RdrOut@@QAEAAVWvfm@@XZ
                       0x2b00  443  ?wvfm@RdrOut@@QBEABVWvfm@@XZ */
  return (Wvfm *)(this + 0x28);
}

//===== 0x10002b20 =====

/* public: class QualCtrl & __thiscall RdrOut::qualctrl(void) */

QualCtrl * __thiscall RdrOut::qualctrl(RdrOut *this)

{
                    /* 0x2b20  322  ?qualctrl@RdrOut@@QAEAAVQualCtrl@@XZ
                       0x2b20  323  ?qualctrl@RdrOut@@QBEABVQualCtrl@@XZ */
  return (QualCtrl *)(this + 0x330);
}

//===== 0x10002b40 =====

/* public: int __thiscall RdrOut::getXOverCut(void)const  */

int __thiscall RdrOut::getXOverCut(RdrOut *this)

{
                    /* 0x2b40  224  ?getXOverCut@RdrOut@@QBEHXZ */
  return *(int *)(this + 0x4e4);
}

//===== 0x10002b60 =====

/* public: __thiscall Annotate::Annotate(void) */

Annotate * __thiscall Annotate::Annotate(Annotate *this)

{
  uint local_8;
  
                    /* 0x2b60  3  ??0Annotate@@QAE@XZ */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x24) = 0;
  *(undefined4 *)(this + 0x28) = 0;
  *(undefined4 *)(this + 0x2c) = 0;
  *(undefined4 *)(this + 0x40) = 0;
  *(undefined4 *)(this + 0x44) = 0;
  *(undefined4 *)(this + 0x48) = 0;
  *(undefined4 *)(this + 0x5c) = 0x100;
  *(undefined4 *)(this + 0x60) = 0;
  *(undefined4 *)(this + 100) = 0;
  *(undefined4 *)(this + 0x68) = 0;
  *(undefined4 *)(this + 0x6c) = 0;
  *(undefined4 *)(this + 0x70) = 0;
  *(undefined4 *)(this + 0x74) = 0xffffffff;
  *(undefined4 *)(this + 0x78) = 0;
  *(undefined4 *)(this + 0x7c) = 0;
  *(undefined4 *)(this + 0x80) = 0;
  *(undefined4 *)(this + 0xa4) = 0;
  *(undefined4 *)(this + 0xa8) = 0;
  *(undefined4 *)(this + 0x3c) = 0;
  *(undefined4 *)(this + 0x38) = 0;
  *(undefined4 *)(this + 0x34) = 0;
  *(undefined4 *)(this + 0x30) = 0;
  *(undefined4 *)(this + 0x48) = 0x411e6666;
  for (local_8 = 0; (int)local_8 < 4; local_8 = local_8 + 1) {
    *(undefined4 *)(this + local_8 * 4 + 0x4c) = 0x411e6666;
  }
  for (local_8 = 0; local_8 < 6; local_8 = local_8 + 1) {
    this[local_8 + 0x1c] = (Annotate)0x0;
  }
  for (local_8 = 0; (int)local_8 < 8; local_8 = local_8 + 1) {
    *(undefined4 *)(this + local_8 * 4 + 0x84) = 0;
  }
  return this;
}

//===== 0x10002d1b =====

/* public: __thiscall Annotate::Annotate(class Annotate const &) */

Annotate * __thiscall Annotate::Annotate(Annotate *this,Annotate *param_1)

{
  uint local_8;
  
                    /* 0x2d1b  2  ??0Annotate@@QAE@ABV0@@Z */
  *(undefined4 *)this = 0x14;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x24) = 0;
  *(undefined4 *)(this + 0x28) = 0;
  *(undefined4 *)(this + 0x2c) = 0;
  *(undefined4 *)(this + 0x40) = 0;
  *(undefined4 *)(this + 0x44) = 0;
  *(undefined4 *)(this + 0x48) = 0;
  *(undefined4 *)(this + 0x5c) = 0x100;
  *(undefined4 *)(this + 0x60) = 0;
  *(undefined4 *)(this + 100) = 0;
  *(undefined4 *)(this + 0x68) = 0;
  *(undefined4 *)(this + 0x6c) = 0;
  *(undefined4 *)(this + 0x70) = 0;
  *(undefined4 *)(this + 0x74) = 0xffffffff;
  *(undefined4 *)(this + 0x78) = 0;
  *(undefined4 *)(this + 0x7c) = 0;
  *(undefined4 *)(this + 0x80) = 0;
  *(undefined4 *)(this + 0xa4) = 0;
  *(undefined4 *)(this + 0xa8) = 0;
  *(undefined4 *)(this + 0x3c) = 0;
  *(undefined4 *)(this + 0x38) = 0;
  *(undefined4 *)(this + 0x34) = 0;
  *(undefined4 *)(this + 0x30) = 0;
  for (local_8 = 0; local_8 < 6; local_8 = local_8 + 1) {
    this[local_8 + 0x1c] = (Annotate)0x0;
  }
  for (local_8 = 0; (int)local_8 < 8; local_8 = local_8 + 1) {
    *(undefined4 *)(this + local_8 * 4 + 0x84) = 0;
  }
  operator=(this,param_1);
  return this;
}

//===== 0x10002eb2 =====

/* private: void __thiscall Annotate::release(void) */

void __thiscall Annotate::release(Annotate *this)

{
  long local_20;
  int local_8;
  
                    /* 0x2eb2  332  ?release@Annotate@@AAEXXZ */
  if (*(int *)(this + 0xc) != 0) {
    operator_delete(*(void **)(this + 0xc));
  }
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  if (*(int *)(this + 0x14) != 0) {
    operator_delete(*(void **)(this + 0x14));
  }
  *(undefined4 *)(this + 0x10) = 0;
  if (*(int *)(this + 0x40) != 0) {
    if (*(int *)(this + 0x2c) < *(int *)(this + 0x28)) {
      local_20 = *(long *)(this + 0x28);
    }
    else {
      local_20 = *(long *)(this + 0x2c);
    }
    free_vector(*(float **)(this + 0x40),1,local_20);
    *(undefined4 *)(this + 0x40) = 0;
  }
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    if (*(int *)(this + local_8 * 4 + 0x30) != 0) {
      free_dmatrix(*(double ***)(this + local_8 * 4 + 0x30),1,*(long *)(this + 0x28),1,
                   *(long *)(this + 0x2c));
      *(undefined4 *)(this + local_8 * 4 + 0x30) = 0;
    }
  }
  if (*(int *)(this + 0x24) != 0) {
    operator_delete(*(void **)(this + 0x24));
  }
  *(undefined4 *)(this + 0x24) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  if (*(int *)(this + 0x60) != 0) {
    free_dmatrix(*(double ***)(this + 0x60),1,4,1,*(long *)(this + 0x5c));
    *(undefined4 *)(this + 0x60) = 0;
  }
  if (*(int *)(this + 100) != 0) {
    free_dmatrix(*(double ***)(this + 100),1,4,1,*(long *)(this + 0x5c));
    *(undefined4 *)(this + 100) = 0;
  }
  if (*(int *)(this + 0xa8) != 0) {
    operator_delete(*(void **)(this + 0xa8));
    *(undefined4 *)(this + 0xa8) = 0;
    *(undefined4 *)(this + 0xa4) = 0;
  }
  return;
}

//===== 0x1000309e =====

/* public: class Annotate const & __thiscall Annotate::operator=(class Annotate const &) */

Annotate * __thiscall Annotate::operator=(Annotate *this,Annotate *param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  void *pvVar4;
  float *pfVar5;
  double **ppdVar6;
  undefined4 *puVar7;
  int iVar8;
  undefined4 *puVar9;
  long local_2c;
  int local_24;
  int local_20;
  int local_14;
  int local_10;
  uint local_c;
  int local_8;
  
                    /* 0x309e  43  ??4Annotate@@QAEABV0@ABV0@@Z */
  if (param_1 != this) {
    release(this);
    *(undefined4 *)(this + 0x68) = *(undefined4 *)(param_1 + 0x68);
    *(undefined4 *)(this + 0x6c) = *(undefined4 *)(param_1 + 0x6c);
    *(undefined4 *)(this + 0x70) = *(undefined4 *)(param_1 + 0x70);
    *(undefined4 *)(this + 0x74) = *(undefined4 *)(param_1 + 0x74);
    *(undefined4 *)(this + 0x78) = *(undefined4 *)(param_1 + 0x78);
    *(undefined4 *)(this + 0x7c) = *(undefined4 *)(param_1 + 0x7c);
    *(undefined4 *)(this + 0x80) = *(undefined4 *)(param_1 + 0x80);
    for (local_c = 0; local_c < 6; local_c = local_c + 1) {
      this[local_c + 0x1c] = param_1[local_c + 0x1c];
    }
    *(undefined4 *)this = *(undefined4 *)param_1;
    if (0 < *(int *)this) {
      *(undefined4 *)(this + 8) = *(undefined4 *)(param_1 + 8);
      pvVar4 = operator_new((*(int *)this + 2) * 0x10);
      *(void **)(this + 0xc) = pvVar4;
      *(undefined4 *)(this + 4) = 0;
      while (*(int *)(this + 4) < *(int *)(param_1 + 4)) {
        puVar7 = (undefined4 *)(*(int *)(param_1 + 0xc) + *(int *)(this + 4) * 0x10);
        puVar9 = (undefined4 *)(*(int *)(this + 0xc) + *(int *)(this + 4) * 0x10);
        *puVar9 = *puVar7;
        puVar9[1] = puVar7[1];
        puVar9[2] = puVar7[2];
        puVar9[3] = puVar7[3];
        *(int *)(this + 4) = *(int *)(this + 4) + 1;
      }
    }
    *(undefined4 *)(this + 0x10) = *(undefined4 *)(param_1 + 0x10);
    if (0 < *(int *)(this + 0x10)) {
      pvVar4 = operator_new((*(int *)(this + 0x10) + 2) * 0xc);
      *(void **)(this + 0x14) = pvVar4;
      for (local_c = 0; (int)local_c < *(int *)(this + 0x10); local_c = local_c + 1) {
        puVar9 = (undefined4 *)(*(int *)(param_1 + 0x14) + local_c * 0xc);
        puVar7 = (undefined4 *)(*(int *)(this + 0x14) + local_c * 0xc);
        *puVar7 = *puVar9;
        puVar7[1] = puVar9[1];
        puVar7[2] = puVar9[2];
      }
    }
    *(undefined4 *)(this + 0x28) = *(undefined4 *)(param_1 + 0x28);
    *(undefined4 *)(this + 0x2c) = *(undefined4 *)(param_1 + 0x2c);
    if ((0 < *(int *)(this + 0x28)) && (0 < *(int *)(this + 0x2c))) {
      if (*(int *)(param_1 + 0x40) != 0) {
        if (*(int *)(this + 0x2c) < *(int *)(this + 0x28)) {
          local_2c = *(long *)(this + 0x28);
        }
        else {
          local_2c = *(long *)(this + 0x2c);
        }
        pfVar5 = vector(1,local_2c);
        *(float **)(this + 0x40) = pfVar5;
        for (local_8 = 1; local_8 <= *(int *)(this + 0x28); local_8 = local_8 + 1) {
          *(undefined4 *)(*(int *)(this + 0x40) + local_8 * 4) =
               *(undefined4 *)(*(int *)(param_1 + 0x40) + local_8 * 4);
        }
      }
      for (local_c = 0; (int)local_c < 4; local_c = local_c + 1) {
        if (*(int *)(param_1 + local_c * 4 + 0x30) != 0) {
          ppdVar6 = dmatrix(1,*(long *)(this + 0x28),1,*(long *)(this + 0x2c));
          *(double ***)(this + local_c * 4 + 0x30) = ppdVar6;
          iVar8 = *(int *)(this + local_c * 4 + 0x30);
          iVar1 = *(int *)(param_1 + local_c * 4 + 0x30);
          for (local_8 = 1; local_8 <= *(int *)(this + 0x28); local_8 = local_8 + 1) {
            for (local_10 = 1; local_10 <= *(int *)(this + 0x2c); local_10 = local_10 + 1) {
              iVar2 = *(int *)(iVar1 + local_8 * 4);
              iVar3 = *(int *)(iVar8 + local_8 * 4);
              *(undefined4 *)(iVar3 + local_10 * 8) = *(undefined4 *)(iVar2 + local_10 * 8);
              *(undefined4 *)(iVar3 + 4 + local_10 * 8) = *(undefined4 *)(iVar2 + 4 + local_10 * 8);
            }
          }
        }
      }
    }
    if ((*(int *)(param_1 + 0x24) != 0) &&
       (*(undefined4 *)(this + 0x18) = *(undefined4 *)(param_1 + 0x18), 0 < *(int *)(this + 0x18)))
    {
      pvVar4 = operator_new((*(int *)(this + 0x18) + 2) * 0x28);
      *(void **)(this + 0x24) = pvVar4;
      for (local_c = 0; (int)local_c < *(int *)(this + 0x18); local_c = local_c + 1) {
        puVar7 = (undefined4 *)(*(int *)(param_1 + 0x24) + local_c * 0x28);
        puVar9 = (undefined4 *)(*(int *)(this + 0x24) + local_c * 0x28);
        for (iVar8 = 10; iVar8 != 0; iVar8 = iVar8 + -1) {
          *puVar9 = *puVar7;
          puVar7 = puVar7 + 1;
          puVar9 = puVar9 + 1;
        }
      }
    }
    if ((*(int *)(param_1 + 0x60) != 0) && (*(int *)(param_1 + 100) != 0)) {
      *(undefined4 *)(this + 0x5c) = *(undefined4 *)(param_1 + 0x5c);
      ppdVar6 = dmatrix(1,4,1,*(long *)(this + 0x5c));
      *(double ***)(this + 0x60) = ppdVar6;
      ppdVar6 = dmatrix(1,4,1,*(long *)(this + 0x5c));
      *(double ***)(this + 100) = ppdVar6;
      for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
        for (local_24 = 1; local_24 <= *(int *)(this + 0x5c); local_24 = local_24 + 1) {
          iVar8 = *(int *)(*(int *)(param_1 + 0x60) + local_20 * 4);
          iVar1 = *(int *)(*(int *)(this + 0x60) + local_20 * 4);
          *(undefined4 *)(iVar1 + local_24 * 8) = *(undefined4 *)(iVar8 + local_24 * 8);
          *(undefined4 *)(iVar1 + 4 + local_24 * 8) = *(undefined4 *)(iVar8 + 4 + local_24 * 8);
          iVar8 = *(int *)(*(int *)(param_1 + 100) + local_20 * 4);
          iVar1 = *(int *)(*(int *)(this + 100) + local_20 * 4);
          *(undefined4 *)(iVar1 + local_24 * 8) = *(undefined4 *)(iVar8 + local_24 * 8);
          *(undefined4 *)(iVar1 + 4 + local_24 * 8) = *(undefined4 *)(iVar8 + 4 + local_24 * 8);
        }
      }
    }
    *(undefined4 *)(this + 0x44) = *(undefined4 *)(param_1 + 0x44);
    *(undefined4 *)(this + 0x48) = *(undefined4 *)(param_1 + 0x48);
    for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
      *(undefined4 *)(this + local_14 * 4 + 0x4c) = *(undefined4 *)(param_1 + local_14 * 4 + 0x4c);
    }
    for (local_c = 0; (int)local_c < 8; local_c = local_c + 1) {
      *(undefined4 *)(this + local_c * 4 + 0x84) = *(undefined4 *)(param_1 + local_c * 4 + 0x84);
    }
    if (*(int *)(param_1 + 0xa8) != 0) {
      *(undefined4 *)(this + 0xa4) = *(undefined4 *)(param_1 + 0xa4);
      pvVar4 = operator_new(*(int *)(this + 0xa4) * 0xc);
      *(void **)(this + 0xa8) = pvVar4;
      for (local_c = 0; (int)local_c < *(int *)(this + 0xa4); local_c = local_c + 1) {
        puVar9 = (undefined4 *)(*(int *)(param_1 + 0xa8) + local_c * 0xc);
        puVar7 = (undefined4 *)(*(int *)(this + 0xa8) + local_c * 0xc);
        *puVar7 = *puVar9;
        puVar7[1] = puVar9[1];
        puVar7[2] = puVar9[2];
      }
    }
  }
  return this;
}

//===== 0x1000365d =====

/* public: __thiscall Annotate::~Annotate(void) */

void __thiscall Annotate::~Annotate(Annotate *this)

{
                    /* 0x365d  30  ??1Annotate@@QAE@XZ */
  release(this);
  return;
}

//===== 0x10003670 =====

/* public: void __thiscall Annotate::recordCurrFix(long,long,int,int) */

void __thiscall
Annotate::recordCurrFix(Annotate *this,long param_1,long param_2,int param_3,int param_4)

{
  void *pvVar1;
  undefined4 *puVar2;
  long *plVar3;
  undefined4 *puVar4;
  int local_c;
  
                    /* 0x3670  331  ?recordCurrFix@Annotate@@QAEXJJHH@Z */
  if (*(int *)this <= *(int *)(this + 4)) {
    if (*(int *)this == 0) {
      *(undefined4 *)this = 5;
    }
    *(int *)this = *(int *)this << 1;
    pvVar1 = operator_new(*(int *)this << 4);
    for (local_c = 0; local_c < *(int *)(this + 4); local_c = local_c + 1) {
      puVar2 = (undefined4 *)(*(int *)(this + 0xc) + local_c * 0x10);
      puVar4 = (undefined4 *)((int)pvVar1 + local_c * 0x10);
      *puVar4 = *puVar2;
      puVar4[1] = puVar2[1];
      puVar4[2] = puVar2[2];
      puVar4[3] = puVar2[3];
    }
    if (*(int *)(this + 0xc) != 0) {
      operator_delete(*(void **)(this + 0xc));
    }
    *(void **)(this + 0xc) = pvVar1;
  }
  plVar3 = (long *)(*(int *)(this + 0xc) + *(int *)(this + 4) * 0x10);
  *(int *)(this + 4) = *(int *)(this + 4) + 1;
  *plVar3 = param_1;
  plVar3[1] = param_2;
  plVar3[2] = param_3;
  plVar3[3] = param_4;
  return;
}

//===== 0x1000377c =====

/* public: void __thiscall Annotate::setMtrxDim(long,long) */

void __thiscall Annotate::setMtrxDim(Annotate *this,long param_1,long param_2)

{
  double **ppdVar1;
  int local_8;
  
                    /* 0x377c  371  ?setMtrxDim@Annotate@@QAEXJJ@Z */
  if (((0 < param_1) && (0 < param_2)) &&
     ((*(int *)(this + 0x28) != param_1 || (*(int *)(this + 0x2c) != param_2)))) {
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      if (*(int *)(this + local_8 * 4 + 0x30) != 0) {
        free_dmatrix(*(double ***)(this + local_8 * 4 + 0x30),1,*(long *)(this + 0x28),1,
                     *(long *)(this + 0x2c));
      }
      ppdVar1 = dmatrix(1,param_1,1,param_2);
      *(double ***)(this + local_8 * 4 + 0x30) = ppdVar1;
    }
    *(long *)(this + 0x28) = param_1;
    *(long *)(this + 0x2c) = param_2;
  }
  return;
}

//===== 0x10003831 =====

/* public: void __thiscall Annotate::setTraces(enum Annotate::TraceId,double * *) */

void __thiscall Annotate::setTraces(Annotate *this,TraceId param_1,double **param_2)

{
  int iVar1;
  double *pdVar2;
  int iVar3;
  int local_10;
  int local_8;
  
                    /* 0x3831  382  ?setTraces@Annotate@@QAEXW4TraceId@1@PAPAN@Z */
  if ((((-1 < (int)param_1) && ((int)param_1 < 4)) && (param_2 != (double **)0x0)) &&
     (*(int *)(this + param_1 * 4 + 0x30) != 0)) {
    iVar1 = *(int *)(this + param_1 * 4 + 0x30);
    for (local_8 = 1; local_8 <= *(int *)(this + 0x2c); local_8 = local_8 + 1) {
      for (local_10 = 1; local_10 <= *(int *)(this + 0x28); local_10 = local_10 + 1) {
        pdVar2 = param_2[local_10];
        iVar3 = *(int *)(iVar1 + local_10 * 4);
        *(undefined4 *)(iVar3 + local_8 * 8) = *(undefined4 *)(pdVar2 + local_8);
        *(undefined4 *)(iVar3 + 4 + local_8 * 8) = *(undefined4 *)((int)pdVar2 + local_8 * 8 + 4);
      }
    }
  }
  return;
}

//===== 0x100038dc =====

void FUN_100038dc(void)

{
  FUN_100038e6();
  return;
}

//===== 0x100038e6 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_100038e6(void)

{
  _DAT_10041a90 = acos(-1.0);
  return;
}

//===== 0x10003900 =====

/* public: void __thiscall Annotate::setCurrent(float const *) */

void __thiscall Annotate::setCurrent(Annotate *this,float *param_1)

{
  float *pfVar1;
  int local_14;
  int local_c;
  
                    /* 0x3900  364  ?setCurrent@Annotate@@QAEXPBM@Z */
  if (*(int *)(this + 0x2c) < *(int *)(this + 0x28)) {
    local_14 = *(int *)(this + 0x28);
  }
  else {
    local_14 = *(int *)(this + 0x2c);
  }
  if (*(int *)(this + 0x40) == 0) {
    pfVar1 = vector(1,local_14);
    *(float **)(this + 0x40) = pfVar1;
  }
  if ((param_1 != (float *)0x0) && (*(int *)(this + 0x40) != 0)) {
    for (local_c = 1; local_c <= local_14; local_c = local_c + 1) {
      *(float *)(*(int *)(this + 0x40) + local_c * 4) = param_1[local_c];
    }
  }
  return;
}

//===== 0x10003996 =====

/* public: void __thiscall Annotate::setCFlen(int) */

void __thiscall Annotate::setCFlen(Annotate *this,int param_1)

{
  void *pvVar1;
  
                    /* 0x3996  362  ?setCFlen@Annotate@@QAEXH@Z */
  if ((*(int *)(this + 0x24) != 0) && (*(int *)(this + 0x18) != param_1)) {
    operator_delete(*(void **)(this + 0x24));
    *(undefined4 *)(this + 0x24) = 0;
  }
  if (*(int *)(this + 0x24) == 0) {
    *(int *)(this + 0x18) = param_1;
    pvVar1 = operator_new((*(int *)(this + 0x18) + 2) * 0x28);
    *(void **)(this + 0x24) = pvVar1;
  }
  return;
}

//===== 0x10003a05 =====

/* public: void __thiscall Annotate::setCFData(int,int,int,int,int,int,int,int,int,int,int) */

void __thiscall
Annotate::setCFData(Annotate *this,int param_1,int param_2,int param_3,int param_4,int param_5,
                   int param_6,int param_7,int param_8,int param_9,int param_10,int param_11)

{
  int *piVar1;
  
                    /* 0x3a05  356  ?setCFData@Annotate@@QAEXHHHHHHHHHHH@Z */
  if (((*(int *)(this + 0x24) != 0) && (-1 < param_1)) && (param_1 < *(int *)(this + 0x18))) {
    piVar1 = (int *)(*(int *)(this + 0x24) + param_1 * 0x28);
    *piVar1 = param_2;
    piVar1[1] = param_3;
    piVar1[2] = param_4;
    piVar1[4] = param_6;
    piVar1[6] = param_8;
    piVar1[8] = param_10;
    piVar1[3] = param_5;
    piVar1[5] = param_7;
    piVar1[7] = param_9;
    piVar1[9] = param_11;
  }
  return;
}

//===== 0x10003a98 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: void __thiscall Annotate::qualifySST(double * *,int,int) */

void __thiscall Annotate::qualifySST(Annotate *this,double **param_1,int param_2,int param_3)

{
  float fVar1;
  int iVar2;
  float *pfVar3;
  double dVar4;
  float local_ac;
  double local_a0;
  double local_98;
  int local_88;
  size_t local_80;
  int local_78;
  double local_74;
  int local_6c;
  int local_64;
  int local_60;
  float local_5c [17];
  int local_18;
  int local_14;
  int local_10;
  int local_c;
  void *local_8;
  
                    /* 0x3a98  324  ?qualifySST@Annotate@@QAEXPAPANHH@Z */
  local_8 = (void *)0x0;
  local_74 = 99.8001;
  local_80 = param_3 - param_2;
  if (1000 < (int)local_80) {
    local_80 = 1000;
  }
  local_8 = operator_new((local_80 + 2) * 0x10);
  if (local_8 != (void *)0x0) {
    local_18 = param_2;
    for (local_60 = 0; local_60 < (int)local_80; local_60 = local_60 + 1) {
      pfVar3 = (float *)((int)local_8 + local_60 * 0x10);
      *(undefined2 *)((int)pfVar3 + 0xe) = 1;
      *pfVar3 = (float)param_1[local_18][1];
      pfVar3[1] = 0.0;
      *(undefined2 *)(pfVar3 + 3) = (undefined2)local_60;
      for (local_88 = 2; local_88 < 5; local_88 = local_88 + 1) {
        fVar1 = (float)param_1[local_18][local_88];
        if (fVar1 <= *pfVar3) {
          if (pfVar3[1] < fVar1) {
            pfVar3[1] = fVar1;
          }
        }
        else {
          pfVar3[1] = *pfVar3;
          *pfVar3 = fVar1;
          *(undefined2 *)((int)pfVar3 + 0xe) = (undefined2)local_88;
        }
      }
      if (pfVar3[1] <= _DAT_1003810c) {
        local_ac = 10.0;
      }
      else {
        local_ac = *pfVar3 / pfVar3[1];
      }
      pfVar3[2] = local_ac;
      local_18 = local_18 + 1;
    }
    qsort(local_8,local_80,0x10,FUN_10003f11);
    local_c = 0;
    for (local_6c = 1; local_64 = local_c, local_6c < 5; local_6c = local_6c + 1) {
      while ((local_64 < (int)local_80 &&
             (*(short *)((int)local_8 + local_64 * 0x10 + 0xe) == local_6c))) {
        local_64 = local_64 + 1;
      }
      if (local_c < local_64) {
        local_64 = local_64 + -1;
      }
      iVar2 = (local_64 - local_c) + 1;
      if (iVar2 == 0) goto LAB_10003ecb;
      local_c = local_64 - iVar2 / 5;
      if (local_c < local_64) {
        qsort((void *)((int)local_8 + local_c * 0x10),(local_64 - local_c) + 1,0x10,FUN_10003f83);
      }
      iVar2 = param_2 + *(short *)((int)local_8 +
                                  (local_c + (((local_64 - local_c) + 1) * 0x4b) / 100) * 0x10 + 0xc
                                  );
      if (_DAT_10038110 == param_1[iVar2][local_6c]) goto LAB_10003ecb;
      for (local_5c[0] = 1.4013e-45; (int)local_5c[0] < 5;
          local_5c[0] = (float)((int)local_5c[0] + 1)) {
        local_5c[(local_6c + -1) * 4 + (int)local_5c[0]] =
             (float)((float10)param_1[iVar2][(int)local_5c[0]] / (float10)param_1[iVar2][local_6c]);
      }
      local_c = local_64 + 1;
    }
    local_74 = 0.0;
    for (local_10 = 0; local_10 < 4; local_10 = local_10 + 1) {
      local_98 = 0.0;
      for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
        if (local_10 != local_14) {
          local_a0 = 0.0;
          for (local_78 = 0; local_78 < 4; local_78 = local_78 + 1) {
            local_a0 = (double)(local_5c[local_10 * 4 + local_78 + 1] *
                                local_5c[local_14 * 4 + local_78 + 1] + (float)local_a0);
          }
          local_98 = local_a0 * local_a0 + local_98;
        }
      }
      dVar4 = sqrt(local_98);
      *(float *)(this + local_10 * 4 + 0x4c) = (float)dVar4;
      local_74 = local_74 + local_98;
    }
  }
LAB_10003ecb:
  dVar4 = sqrt(local_74);
  *(float *)(this + 0x48) = (float)dVar4;
  if (local_8 != (void *)0x0) {
    operator_delete(local_8);
  }
  return;
}

//===== 0x10003f11 =====

undefined4 __cdecl FUN_10003f11(float *param_1,float *param_2)

{
  undefined4 uVar1;
  
  if (*(short *)((int)param_2 + 0xe) < *(short *)((int)param_1 + 0xe)) {
    uVar1 = 1;
  }
  else if (*(short *)((int)param_1 + 0xe) < *(short *)((int)param_2 + 0xe)) {
    uVar1 = 0xffffffff;
  }
  else if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x10003f83 =====

undefined4 __cdecl FUN_10003f83(int param_1,int param_2)

{
  undefined4 uVar1;
  
  if (*(float *)(param_1 + 8) <= *(float *)(param_2 + 8)) {
    if (*(float *)(param_2 + 8) <= *(float *)(param_1 + 8)) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x10003fc7 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: void __thiscall Annotate::measRawRes(double * *,int,int) */

void __thiscall Annotate::measRawRes(Annotate *this,double **param_1,int param_2,int param_3)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  int iVar5;
  float *pfVar6;
  void *pvVar7;
  float *pfVar8;
  void *pvVar9;
  float fVar10;
  int iVar11;
  int *piVar12;
  undefined4 *puVar13;
  undefined4 *puVar14;
  int local_6c;
  float local_60;
  int local_3c;
  int local_38;
  int local_34;
  int local_2c;
  size_t local_28;
  int local_1c;
  int local_18;
  size_t local_14;
  float local_10;
  int local_8;
  
                    /* 0x3fc7  278  ?measRawRes@Annotate@@QAEXPAPANHH@Z */
  pfVar6 = vector(1,param_3);
  pvVar7 = operator_new(param_3 * 0x14);
  for (local_28 = 0; (int)local_28 < ((param_3 - param_2) + 1) / 2; local_28 = local_28 + 1) {
    puVar13 = &DAT_100380f8;
    puVar14 = (undefined4 *)((int)pvVar7 + local_28 * 0x14);
    for (iVar11 = 5; iVar11 != 0; iVar11 = iVar11 + -1) {
      *puVar14 = *puVar13;
      puVar13 = puVar13 + 1;
      puVar14 = puVar14 + 1;
    }
  }
  for (local_2c = param_2; local_2c <= param_3; local_2c = local_2c + 1) {
    pfVar6[local_2c] = (float)param_1[local_2c][1];
    for (local_18 = 2; local_18 < 5; local_18 = local_18 + 1) {
      if (pfVar6[local_2c] < (float)param_1[local_2c][local_18]) {
        pfVar6[local_2c] = (float)param_1[local_2c][local_18];
      }
    }
  }
  pfVar8 = vector(1,param_3);
  local_38 = 0;
  for (local_2c = param_2 + DAT_1003f204; local_2c <= param_3 - DAT_1003f204;
      local_2c = local_2c + 1) {
    if (local_38 < local_2c - DAT_1003f204) {
      local_38 = local_2c - DAT_1003f204;
      local_10 = pfVar6[local_38];
      local_8 = local_38;
      while (local_8 = local_8 + 1, local_8 <= local_2c + DAT_1003f204) {
        if (local_10 <= pfVar6[local_8]) {
          local_38 = local_8;
          local_10 = pfVar6[local_8];
        }
      }
    }
    else if (local_10 <= pfVar6[local_2c + DAT_1003f204]) {
      local_38 = local_2c + DAT_1003f204;
      local_10 = pfVar6[local_38];
    }
    pfVar8[local_2c] = local_10 / _DAT_10038118;
  }
  for (local_8 = 1; local_8 < DAT_1003f204; local_8 = local_8 + 1) {
    pfVar8[param_2 + local_8] = pfVar8[param_2 + DAT_1003f204];
    pfVar8[param_3 - local_8] = pfVar8[param_3 - DAT_1003f204];
  }
  local_28 = 0;
  local_3c = 1;
  do {
    iVar11 = param_2;
    if (4 < local_3c) {
      free_vector(pfVar8,1,param_3);
      qsort((void *)((int)pvVar7 + 0x14),local_28,0x14,FUN_10004739);
      *(size_t *)(this + 0x10) = local_28;
      pvVar9 = operator_new(local_28 * 0xc);
      *(void **)(this + 0x14) = pvVar9;
      local_2c = 1;
      do {
        if ((int)local_28 < local_2c) {
          for (local_2c = 1; local_2c <= (int)local_28; local_2c = local_2c + 1) {
            pfVar8 = (float *)(*(int *)(this + 0x14) + (local_2c + -1) * 0xc);
            local_34 = local_2c + -5;
            local_14 = local_2c + 5;
            if (local_34 < 1) {
              local_34 = 1;
            }
            if ((int)local_28 < (int)local_14) {
              local_14 = local_28;
            }
            local_60 = 0.0;
            local_6c = 0;
            for (local_1c = local_34; local_1c <= (int)local_14; local_1c = local_1c + 1) {
              if (*(int *)((int)pvVar7 + local_1c * 0x14 + 0xc) != 0) {
                local_60 = (float)*(int *)((int)pvVar7 + local_1c * 0x14 + 0xc) + local_60;
                local_6c = local_6c + 1;
              }
            }
            *pfVar8 = local_60 / (float)local_6c;
            fVar10 = (float)ftol();
            pfVar8[1] = fVar10;
            pfVar8[2] = *(float *)((int)pvVar7 + local_2c * 0x14 + 4);
          }
          free_vector(pfVar6,1,param_3);
          operator_delete(pvVar7);
          return;
        }
        piVar12 = (int *)((int)pvVar7 + local_2c * 0x14);
        if (piVar12[1] != 0) {
          local_34 = *piVar12 * 2 - piVar12[1];
          local_14 = piVar12[2] * 2 - piVar12[1];
          if (local_34 < param_2) {
            local_34 = param_2;
          }
          if (param_3 < (int)local_14) {
            local_14 = param_3;
          }
          uVar1 = *(undefined4 *)(param_1[piVar12[1]] + piVar12[4]);
          uVar2 = *(undefined4 *)((int)param_1[piVar12[1]] + piVar12[4] * 8 + 4);
          piVar12[3] = 2;
          iVar11 = piVar12[1];
          while (local_1c = iVar11 + -1, local_34 <= local_1c) {
            uVar3 = *(undefined4 *)(param_1[local_1c] + piVar12[4]);
            uVar4 = *(undefined4 *)((int)param_1[local_1c] + piVar12[4] * 8 + 4);
            if ((param_1[iVar11][piVar12[4]] < (double)CONCAT44(uVar4,uVar3)) ||
               ((double)CONCAT44(uVar4,uVar3) <= (double)CONCAT44(uVar2,uVar1) / _DAT_10038120))
            break;
            piVar12[3] = piVar12[3] + 1;
            iVar11 = local_1c;
          }
          iVar11 = piVar12[1];
          while (local_1c = iVar11 + 1, local_1c <= (int)local_14) {
            uVar3 = *(undefined4 *)(param_1[local_1c] + piVar12[4]);
            uVar4 = *(undefined4 *)((int)param_1[local_1c] + piVar12[4] * 8 + 4);
            if ((param_1[iVar11][piVar12[4]] < (double)CONCAT44(uVar4,uVar3)) ||
               ((double)CONCAT44(uVar4,uVar3) <= (double)CONCAT44(uVar2,uVar1) / _DAT_10038120))
            break;
            piVar12[3] = piVar12[3] + 1;
            iVar11 = local_1c;
          }
        }
        local_2c = local_2c + 1;
      } while( true );
    }
LAB_1000424d:
    iVar5 = iVar11;
    local_2c = iVar5 + 1;
    if (local_2c < param_3) {
      uVar1 = *(undefined4 *)(param_1[local_2c] + local_3c);
      uVar2 = *(undefined4 *)((int)param_1[local_2c] + local_3c * 8 + 4);
      iVar11 = local_2c;
      if (((pfVar8[local_2c] < (float)(double)CONCAT44(uVar2,uVar1)) &&
          (iVar11 = local_2c, param_1[iVar5][local_3c] < (double)CONCAT44(uVar2,uVar1))) &&
         (iVar11 = local_2c, param_1[iVar5 + 2][local_3c] < (double)CONCAT44(uVar2,uVar1))) {
        if (param_3 <= (int)local_28) goto LAB_10004226;
        local_28 = local_28 + 1;
        *(int *)((int)pvVar7 + local_28 * 0x14 + 4) = local_2c;
        *(int *)((int)pvVar7 + local_28 * 0x14 + 0x10) = local_3c;
        for (local_8 = iVar5; param_2 < local_8; local_8 = local_8 + -1) {
          if (((float)param_1[local_8][local_3c] < pfVar8[local_2c]) ||
             (param_1[local_8 + 1][local_3c] <= param_1[local_8][local_3c])) {
            *(int *)((int)pvVar7 + local_28 * 0x14) = local_8;
            break;
          }
        }
        for (local_8 = iVar5 + 2; iVar11 = local_8, local_8 < param_3; local_8 = local_8 + 1) {
          if (((float)param_1[local_8][local_3c] < pfVar8[local_2c]) ||
             (param_1[local_8 + -1][local_3c] <= param_1[local_8][local_3c])) {
            *(int *)((int)pvVar7 + local_28 * 0x14 + 8) = local_8;
            iVar11 = local_8;
            break;
          }
        }
      }
      goto LAB_1000424d;
    }
LAB_10004226:
    local_3c = local_3c + 1;
  } while( true );
}

//===== 0x10004739 =====

int __cdecl FUN_10004739(int param_1,int param_2)

{
  return *(int *)(param_1 + 4) - *(int *)(param_2 + 4);
}

//===== 0x1000474a =====

/* public: void __thiscall Annotate::getSpecSepQual(float &,float * const)const  */

void __thiscall Annotate::getSpecSepQual(Annotate *this,float *param_1,float *param_2)

{
  int local_8;
  
                    /* 0x474a  219  ?getSpecSepQual@Annotate@@QBEXAAMQAM@Z */
  *param_1 = *(float *)(this + 0x48);
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    param_2[local_8] = *(float *)(this + local_8 * 4 + 0x4c);
  }
  return;
}

//===== 0x10004793 =====

/* public: void __thiscall Annotate::setSpecSepQual(float,float * const) */

void __thiscall Annotate::setSpecSepQual(Annotate *this,float param_1,float *param_2)

{
  int local_8;
  
                    /* 0x4793  379  ?setSpecSepQual@Annotate@@QAEXMQAM@Z */
  *(float *)(this + 0x48) = param_1;
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    *(float *)(this + local_8 * 4 + 0x4c) = param_2[local_8];
  }
  return;
}

//===== 0x100047da =====

/* public: void __thiscall Annotate::getCFData(int,int &,int &,int &,int &,int &,int &,int &,int
   &,int &,int &)const  */

void __thiscall
Annotate::getCFData(Annotate *this,int param_1,int *param_2,int *param_3,int *param_4,int *param_5,
                   int *param_6,int *param_7,int *param_8,int *param_9,int *param_10,int *param_11)

{
  int *piVar1;
  
                    /* 0x47da  177  ?getCFData@Annotate@@QBEXHAAH000000000@Z */
  if (((*(int *)(this + 0x24) != 0) && (-1 < param_1)) && (param_1 < *(int *)(this + 0x18))) {
    piVar1 = (int *)(*(int *)(this + 0x24) + param_1 * 0x28);
    *param_2 = *piVar1;
    *param_3 = piVar1[1];
    *param_4 = piVar1[2];
    *param_6 = piVar1[4];
    *param_8 = piVar1[6];
    *param_10 = piVar1[8];
    *param_5 = piVar1[3];
    *param_7 = piVar1[5];
    *param_9 = piVar1[7];
    *param_11 = piVar1[9];
  }
  return;
}

//===== 0x10004889 =====

/* public: void __thiscall Annotate::setMobTbl(struct MobCtrlTbl const *,int) */

void __thiscall Annotate::setMobTbl(Annotate *this,MobCtrlTbl *param_1,int param_2)

{
  void *pvVar1;
  MobCtrlTbl *pMVar2;
  undefined4 *puVar3;
  int local_8;
  
                    /* 0x4889  370  ?setMobTbl@Annotate@@QAEXPBUMobCtrlTbl@@H@Z */
  if (*(int *)(this + 0xa8) != 0) {
    operator_delete(*(void **)(this + 0xa8));
    *(undefined4 *)(this + 0xa8) = 0;
    *(undefined4 *)(this + 0xa4) = 0;
  }
  if (0 < param_2) {
    *(int *)(this + 0xa4) = param_2;
    pvVar1 = operator_new(param_2 * 0xc);
    *(void **)(this + 0xa8) = pvVar1;
    for (local_8 = 0; local_8 < *(int *)(this + 0xa4); local_8 = local_8 + 1) {
      pMVar2 = param_1 + local_8 * 0xc;
      puVar3 = (undefined4 *)(*(int *)(this + 0xa8) + local_8 * 0xc);
      *puVar3 = *(undefined4 *)pMVar2;
      puVar3[1] = *(undefined4 *)(pMVar2 + 4);
      puVar3[2] = *(undefined4 *)(pMVar2 + 8);
    }
  }
  return;
}

//===== 0x1000494e =====

/* public: void __thiscall Annotate::getMobTblEntry(int,struct MobCtrlTbl &)const  */

void __thiscall Annotate::getMobTblEntry(Annotate *this,int param_1,MobCtrlTbl *param_2)

{
  undefined4 *puVar1;
  
                    /* 0x494e  192  ?getMobTblEntry@Annotate@@QBEXHAAUMobCtrlTbl@@@Z */
  if ((-1 < param_1) && (param_1 < *(int *)(this + 0xa4))) {
    puVar1 = (undefined4 *)(*(int *)(this + 0xa8) + param_1 * 0xc);
    *(undefined4 *)param_2 = *puVar1;
    *(undefined4 *)(param_2 + 4) = puVar1[1];
    *(undefined4 *)(param_2 + 8) = puVar1[2];
  }
  return;
}

//===== 0x100049a0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall RdrOut::bandqual(void) */

void __thiscall RdrOut::bandqual(RdrOut *this)

{
  double dVar1;
  double dVar2;
  double dVar3;
  double dVar4;
  double dVar5;
  double dVar6;
  double dVar7;
  double dVar8;
  double dVar9;
  double dVar10;
  double dVar11;
  double dVar12;
  double dVar13;
  char cVar14;
  int iVar15;
  undefined4 *puVar16;
  undefined4 *puVar17;
  undefined4 *puVar18;
  undefined4 *puVar19;
  undefined4 *puVar20;
  undefined4 *puVar21;
  undefined4 *puVar22;
  undefined4 *puVar23;
  undefined4 *puVar24;
  undefined4 *puVar25;
  undefined4 *puVar26;
  undefined4 *puVar27;
  undefined4 *puVar28;
  undefined4 *puVar29;
  undefined4 *puVar30;
  undefined4 *puVar31;
  undefined4 *puVar32;
  undefined4 *puVar33;
  undefined4 *puVar34;
  undefined4 *puVar35;
  undefined4 *puVar36;
  float10 fVar37;
  float10 fVar38;
  float fVar39;
  undefined4 local_8c4;
  undefined4 local_8bc;
  undefined4 local_8ac;
  undefined4 local_8a4;
  undefined4 local_894;
  uint local_874;
  uint local_86c;
  double local_864;
  undefined4 local_85c;
  double local_844;
  undefined4 local_83c;
  double local_824;
  double local_804;
  undefined4 local_7e4;
  undefined4 local_7c4;
  double local_7bc;
  double local_7b4;
  undefined4 local_7ac;
  double local_79c;
  double local_794;
  uint local_784;
  uint local_774;
  uint local_76c;
  double local_75c;
  uint local_73c;
  uint local_72c;
  uint local_724;
  double local_6fc;
  double local_6f4;
  double local_6ec;
  double local_6e4;
  double local_6dc;
  double local_6d4;
  double local_6cc;
  double local_68c;
  double local_67c;
  double local_66c;
  double local_664;
  double local_65c;
  double local_654;
  double local_644;
  double local_634;
  double local_62c;
  double local_624;
  double local_61c;
  double local_60c;
  double local_5fc;
  double local_5f4;
  double local_5ec;
  double local_5e4;
  double local_5d4;
  double local_5c4;
  double local_5bc;
  double local_5b4;
  double local_4b4;
  double local_4a4;
  double local_494;
  double local_484;
  double local_47c;
  double local_46c;
  double local_45c;
  double local_44c;
  double local_444;
  double local_434;
  double local_424;
  double local_414;
  double local_40c;
  double local_3fc;
  double local_3ec;
  double local_3dc;
  double local_3d4;
  double local_3c4;
  double local_3b4;
  double local_3a4;
  double local_39c;
  double local_38c;
  double local_37c;
  double local_36c;
  undefined4 local_34c;
  double local_314;
  double local_2cc;
  double local_2ac;
  double local_28c;
  double local_274;
  double local_254;
  double local_19c;
  undefined4 local_18c;
  undefined4 local_17c;
  uint local_174;
  uint local_16c;
  double local_164;
  double local_15c;
  double local_148;
  uint local_100;
  undefined4 local_f4;
  uint local_84;
  undefined4 local_5c;
  int local_8;
  
                    /* 0x49a0  78  ?bandqual@RdrOut@@AAEXXZ */
  iVar15 = Wvfm::annotate((Wvfm *)(this + 0x1c));
  puVar16 = FUN_10012ad0(3,&DAT_10038130,&DAT_10038148,0);
  puVar17 = FUN_10012ad0(4,&DAT_10038160,&DAT_10038180,0);
  puVar18 = FUN_10012ad0(4,&DAT_100381a0,&DAT_100381c0,0);
  puVar19 = FUN_10012ad0(4,&DAT_100381e0,&DAT_10038200,0);
  puVar20 = FUN_10012ad0(3,&DAT_10038220,&DAT_10038238,0);
  puVar21 = FUN_10012ad0(2,&DAT_10038250,&DAT_10038260,0);
  puVar22 = FUN_10012ad0(2,&DAT_10038270,&DAT_10038280,0);
  puVar23 = FUN_10012ad0(4,&DAT_10038290,&DAT_100382b0,0);
  puVar24 = FUN_10012ad0(3,&DAT_100382d0,&DAT_100382e8,0);
  puVar25 = FUN_10012ad0(3,&DAT_10038300,&DAT_10038318,0);
  puVar26 = FUN_10012ad0(3,&DAT_10038330,&DAT_10038348,0);
  for (local_8 = 0; local_8 < iVar15; local_8 = local_8 + 1) {
    puVar27 = FUN_10012ad0(2,&DAT_10038450,&DAT_10038460,0);
    puVar28 = FUN_10012ad0(3,&DAT_10038360,&DAT_10038438,0);
    puVar29 = FUN_10012ad0(3,&DAT_10038378,&DAT_10038438,0);
    puVar30 = FUN_10012ad0(3,&DAT_10038390,&DAT_10038438,0);
    puVar31 = FUN_10012ad0(3,&DAT_100383a8,&DAT_10038438,0);
    puVar32 = FUN_10012ad0(3,&DAT_100383c0,&DAT_10038438,0);
    puVar33 = FUN_10012ad0(3,&DAT_100383d8,&DAT_10038438,0);
    puVar34 = FUN_10012ad0(3,&DAT_100383f0,&DAT_10038438,0);
    puVar35 = FUN_10012ad0(3,&DAT_10038408,&DAT_10038438,0);
    puVar36 = FUN_10012ad0(3,&DAT_10038420,&DAT_10038438,0);
    fVar39 = BandStatArray::hght((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar16[3])(puVar16,(double)fVar39);
    dVar1 = (double)fVar37;
    fVar39 = BandStatArray::hght((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar17[3])(puVar17,(double)fVar39);
    dVar2 = (double)fVar37;
    fVar39 = BandStatArray::hght((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar18[3])(puVar18,(double)fVar39);
    dVar3 = (double)fVar37;
    fVar39 = BandStatArray::hght((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar19[3])(puVar19,(double)fVar39);
    dVar4 = (double)fVar37;
    fVar39 = BandStatArray::hght((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar20[3])(puVar20,(double)fVar39);
    dVar5 = (double)fVar37;
    fVar39 = BandStatArray::xbnd((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar21[3])(puVar21,(double)fVar39);
    dVar6 = (double)fVar37;
    fVar39 = BandStatArray::xbnd((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar22[3])(puVar22,(double)fVar39);
    dVar7 = (double)fVar37;
    fVar39 = BandStatArray::widt((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar23[3])(puVar23,(double)fVar39);
    local_6f4 = (double)fVar37;
    fVar39 = BandStatArray::shap((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar24[3])(puVar24,(double)fVar39);
    dVar8 = (double)fVar37;
    fVar39 = BandStatArray::buzz((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar26[3])(puVar26,(double)fVar39);
    dVar9 = (double)fVar37;
    fVar39 = BandStatArray::sgap((BandStatArray *)(this + 0x1c),local_8);
    fVar37 = (float10)(*(code *)puVar25[3])(puVar25,(double)fVar39);
    fVar39 = BandStatArray::lgap((BandStatArray *)(this + 0x1c),local_8);
    fVar38 = (float10)(*(code *)puVar25[3])(puVar25,(double)fVar39);
    local_6fc = (double)fVar38;
    if ((double)fVar37 < local_6fc) {
      local_6fc = (double)fVar37;
    }
    local_15c = dVar1;
    if (_DAT_10038470 - local_6fc <= dVar1) {
      local_15c = _DAT_10038470 - local_6fc;
    }
    (*(code *)puVar28[7])(puVar28,local_15c._0_4_);
    local_164 = dVar6;
    if (_DAT_10038470 - local_6fc <= dVar6) {
      local_164 = _DAT_10038470 - local_6fc;
    }
    local_100 = SUB84(dVar2,0);
    if (local_164 <= dVar2) {
      if (_DAT_10038470 - local_6fc <= dVar6) {
        local_174 = SUB84(_DAT_10038470 - local_6fc,0);
      }
      else {
        local_174 = SUB84(dVar6,0);
      }
      local_16c = local_174;
    }
    else {
      local_16c = local_100;
    }
    (*(code *)puVar29[7])(puVar29,local_16c);
    dVar10 = local_6fc;
    if (dVar1 < local_6fc) {
      dVar10 = dVar1;
    }
    local_17c = SUB84(dVar10,0);
    (*(code *)puVar30[7])(puVar30,local_17c);
    dVar1 = dVar5;
    if (dVar5 < dVar4) {
      dVar1 = dVar4;
    }
    local_84 = SUB84(dVar3,0);
    dVar10 = dVar3;
    if ((dVar3 <= dVar1) && (dVar10 = dVar5, dVar5 < dVar4)) {
      dVar10 = dVar4;
    }
    local_18c = SUB84(dVar10,0);
    local_19c = dVar10;
    if (_DAT_10038470 - dVar8 < dVar10) {
      local_19c = _DAT_10038470 - dVar8;
    }
    local_f4 = SUB84(dVar9,0);
    dVar1 = local_6fc;
    if (dVar9 < local_6fc) {
      dVar1 = dVar9;
    }
    dVar4 = local_6f4;
    if ((dVar1 <= local_6f4) && (dVar4 = local_6fc, dVar9 < local_6fc)) {
      dVar4 = dVar9;
    }
    dVar1 = dVar7;
    if (dVar4 <= dVar7) {
      dVar4 = local_6fc;
      if (dVar9 < local_6fc) {
        dVar4 = dVar9;
      }
      dVar1 = local_6f4;
      if ((dVar4 <= local_6f4) && (dVar1 = local_6fc, dVar9 < local_6fc)) {
        dVar1 = dVar9;
      }
    }
    if (dVar1 <= local_19c) {
      dVar1 = local_6fc;
      if (dVar9 < local_6fc) {
        dVar1 = dVar9;
      }
      dVar4 = local_6f4;
      if ((dVar1 <= local_6f4) && (dVar4 = local_6fc, dVar9 < local_6fc)) {
        dVar4 = dVar9;
      }
      local_19c = dVar7;
      if (dVar4 <= dVar7) {
        dVar1 = local_6fc;
        if (dVar9 < local_6fc) {
          dVar1 = dVar9;
        }
        local_19c = local_6f4;
        if ((dVar1 <= local_6f4) && (local_19c = local_6fc, dVar9 < local_6fc)) {
          local_19c = dVar9;
        }
      }
    }
    dVar1 = local_6fc;
    if (dVar8 < local_6fc) {
      dVar1 = dVar8;
    }
    dVar4 = local_6f4;
    if ((dVar1 <= local_6f4) && (dVar4 = local_6fc, dVar8 < local_6fc)) {
      dVar4 = dVar8;
    }
    dVar1 = dVar9;
    if (dVar4 <= dVar9) {
      dVar4 = local_6fc;
      if (dVar8 < local_6fc) {
        dVar4 = dVar8;
      }
      dVar1 = local_6f4;
      if ((dVar4 <= local_6f4) && (dVar1 = local_6fc, dVar8 < local_6fc)) {
        dVar1 = dVar8;
      }
    }
    local_254 = dVar8;
    if (_DAT_10038470 - local_6fc <= dVar8) {
      local_254 = _DAT_10038470 - local_6fc;
    }
    dVar4 = local_6f4;
    if ((local_254 <= local_6f4) && (dVar4 = dVar8, _DAT_10038470 - local_6fc <= dVar8)) {
      dVar4 = _DAT_10038470 - local_6fc;
    }
    dVar5 = dVar9;
    if (dVar4 <= dVar9) {
      local_274 = dVar8;
      if (_DAT_10038470 - local_6fc <= dVar8) {
        local_274 = _DAT_10038470 - local_6fc;
      }
      dVar5 = local_6f4;
      if ((local_274 <= local_6f4) && (dVar5 = dVar8, _DAT_10038470 - local_6fc <= dVar8)) {
        dVar5 = _DAT_10038470 - local_6fc;
      }
    }
    local_28c = local_6fc;
    if (_DAT_10038470 - dVar8 < local_6fc) {
      local_28c = _DAT_10038470 - dVar8;
    }
    dVar4 = local_6f4;
    if ((local_28c <= local_6f4) && (dVar4 = local_6fc, _DAT_10038470 - dVar8 < local_6fc)) {
      dVar4 = _DAT_10038470 - dVar8;
    }
    dVar11 = dVar9;
    if (dVar4 <= dVar9) {
      local_2ac = local_6fc;
      if (_DAT_10038470 - dVar8 < local_6fc) {
        local_2ac = _DAT_10038470 - dVar8;
      }
      dVar11 = local_6f4;
      if ((local_2ac <= local_6f4) && (dVar11 = local_6fc, _DAT_10038470 - dVar8 < local_6fc)) {
        dVar11 = _DAT_10038470 - dVar8;
      }
    }
    dVar4 = local_6fc;
    if (dVar8 < local_6fc) {
      dVar4 = dVar8;
    }
    if (dVar4 <= _DAT_10038470 - local_6f4) {
      local_2cc = local_6fc;
      if (dVar8 < local_6fc) {
        local_2cc = dVar8;
      }
    }
    else {
      local_2cc = _DAT_10038470 - local_6f4;
    }
    dVar4 = dVar9;
    if (local_2cc <= dVar9) {
      dVar4 = local_6fc;
      if (dVar8 < local_6fc) {
        dVar4 = dVar8;
      }
      if (dVar4 <= _DAT_10038470 - local_6f4) {
        dVar4 = local_6fc;
        if (dVar8 < local_6fc) {
          dVar4 = dVar8;
        }
      }
      else {
        dVar4 = _DAT_10038470 - local_6f4;
      }
    }
    dVar12 = local_6fc;
    if (dVar8 < local_6fc) {
      dVar12 = dVar8;
    }
    dVar13 = local_6f4;
    if ((dVar12 <= local_6f4) && (dVar13 = local_6fc, dVar8 < local_6fc)) {
      dVar13 = dVar8;
    }
    if (dVar13 <= _DAT_10038470 - dVar9) {
      dVar12 = local_6fc;
      if (dVar8 < local_6fc) {
        dVar12 = dVar8;
      }
      local_314 = local_6f4;
      if ((dVar12 <= local_6f4) && (local_314 = local_6fc, dVar8 < local_6fc)) {
        local_314 = dVar8;
      }
    }
    else {
      local_314 = _DAT_10038470 - dVar9;
    }
    dVar12 = local_314;
    if (local_314 < dVar4) {
      dVar12 = dVar4;
    }
    dVar13 = dVar11;
    if ((dVar11 <= dVar12) && (dVar13 = local_314, local_314 < dVar4)) {
      dVar13 = dVar4;
    }
    if (dVar5 <= dVar13) {
      dVar12 = local_314;
      if (local_314 < dVar4) {
        dVar12 = dVar4;
      }
      dVar5 = dVar11;
      if ((dVar11 <= dVar12) && (dVar5 = local_314, local_314 < dVar4)) {
        dVar5 = dVar4;
      }
    }
    local_34c = SUB84(dVar5,0);
    local_36c = local_6fc;
    if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
      local_36c = dVar8;
    }
    local_36c = _DAT_10038470 - local_36c;
    local_37c = local_6f4;
    if (local_36c <= local_6f4) {
      local_37c = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_37c = dVar8;
      }
      local_37c = _DAT_10038470 - local_37c;
    }
    local_39c = dVar9;
    if (local_37c <= dVar9) {
      local_38c = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_38c = dVar8;
      }
      local_38c = _DAT_10038470 - local_38c;
      local_39c = local_6f4;
      if (local_38c <= local_6f4) {
        local_39c = local_6fc;
        if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
          local_39c = dVar8;
        }
        local_39c = _DAT_10038470 - local_39c;
      }
    }
    local_3a4 = local_6fc;
    if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
      local_3a4 = local_6f4;
    }
    local_3a4 = _DAT_10038470 - local_3a4;
    local_3b4 = dVar8;
    if (local_3a4 <= dVar8) {
      local_3b4 = local_6fc;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
        local_3b4 = local_6f4;
      }
      local_3b4 = _DAT_10038470 - local_3b4;
    }
    local_3d4 = dVar9;
    if (local_3b4 <= dVar9) {
      local_3c4 = local_6fc;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
        local_3c4 = local_6f4;
      }
      local_3c4 = _DAT_10038470 - local_3c4;
      local_3d4 = dVar8;
      if (local_3c4 <= dVar8) {
        local_3d4 = local_6fc;
        if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
          local_3d4 = local_6f4;
        }
        local_3d4 = _DAT_10038470 - local_3d4;
      }
    }
    local_3dc = dVar8;
    if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
      local_3dc = local_6f4;
    }
    local_3dc = _DAT_10038470 - local_3dc;
    local_3ec = local_6fc;
    if (local_3dc <= local_6fc) {
      local_3ec = dVar8;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
        local_3ec = local_6f4;
      }
      local_3ec = _DAT_10038470 - local_3ec;
    }
    local_40c = dVar9;
    if (local_3ec <= dVar9) {
      local_3fc = dVar8;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
        local_3fc = local_6f4;
      }
      local_3fc = _DAT_10038470 - local_3fc;
      local_40c = local_6fc;
      if (local_3fc <= local_6fc) {
        local_40c = dVar8;
        if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
          local_40c = local_6f4;
        }
        local_40c = _DAT_10038470 - local_40c;
      }
    }
    local_414 = local_6fc;
    if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6fc) {
      local_414 = dVar9;
    }
    local_414 = _DAT_10038470 - local_414;
    local_424 = dVar8;
    if (local_414 <= dVar8) {
      local_424 = local_6fc;
      if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6fc) {
        local_424 = dVar9;
      }
      local_424 = _DAT_10038470 - local_424;
    }
    local_444 = local_6f4;
    if (local_424 <= local_6f4) {
      local_434 = local_6fc;
      if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6fc) {
        local_434 = dVar9;
      }
      local_434 = _DAT_10038470 - local_434;
      local_444 = dVar8;
      if (local_434 <= dVar8) {
        local_444 = local_6fc;
        if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6fc) {
          local_444 = dVar9;
        }
        local_444 = _DAT_10038470 - local_444;
      }
    }
    local_44c = dVar8;
    if (_DAT_10038470 - dVar9 < _DAT_10038470 - dVar8) {
      local_44c = dVar9;
    }
    local_44c = _DAT_10038470 - local_44c;
    local_45c = local_6fc;
    if (local_44c <= local_6fc) {
      local_45c = dVar8;
      if (_DAT_10038470 - dVar9 < _DAT_10038470 - dVar8) {
        local_45c = dVar9;
      }
      local_45c = _DAT_10038470 - local_45c;
    }
    local_47c = local_6f4;
    if (local_45c <= local_6f4) {
      local_46c = dVar8;
      if (_DAT_10038470 - dVar9 < _DAT_10038470 - dVar8) {
        local_46c = dVar9;
      }
      local_46c = _DAT_10038470 - local_46c;
      local_47c = local_6fc;
      if (local_46c <= local_6fc) {
        local_47c = dVar8;
        if (_DAT_10038470 - dVar9 < _DAT_10038470 - dVar8) {
          local_47c = dVar9;
        }
        local_47c = _DAT_10038470 - local_47c;
      }
    }
    local_484 = local_6f4;
    if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6f4) {
      local_484 = dVar9;
    }
    local_484 = _DAT_10038470 - local_484;
    local_494 = local_6fc;
    if (local_484 <= local_6fc) {
      local_494 = local_6f4;
      if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6f4) {
        local_494 = dVar9;
      }
      local_494 = _DAT_10038470 - local_494;
    }
    local_4b4 = dVar8;
    if (local_494 <= dVar8) {
      local_4a4 = local_6f4;
      if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6f4) {
        local_4a4 = dVar9;
      }
      local_4a4 = _DAT_10038470 - local_4a4;
      local_4b4 = local_6fc;
      if (local_4a4 <= local_6fc) {
        local_4b4 = local_6f4;
        if (_DAT_10038470 - dVar9 < _DAT_10038470 - local_6f4) {
          local_4b4 = dVar9;
        }
        local_4b4 = _DAT_10038470 - local_4b4;
      }
    }
    dVar4 = local_4b4;
    if (local_4b4 < local_47c) {
      dVar4 = local_47c;
    }
    dVar11 = local_444;
    if ((local_444 <= dVar4) && (dVar11 = local_4b4, local_4b4 < local_47c)) {
      dVar11 = local_47c;
    }
    dVar4 = local_40c;
    if (local_40c <= dVar11) {
      dVar11 = local_4b4;
      if (local_4b4 < local_47c) {
        dVar11 = local_47c;
      }
      dVar4 = local_444;
      if ((local_444 <= dVar11) && (dVar4 = local_4b4, local_4b4 < local_47c)) {
        dVar4 = local_47c;
      }
    }
    dVar11 = local_3d4;
    if (local_3d4 <= dVar4) {
      dVar4 = local_4b4;
      if (local_4b4 < local_47c) {
        dVar4 = local_47c;
      }
      dVar12 = local_444;
      if ((local_444 <= dVar4) && (dVar12 = local_4b4, local_4b4 < local_47c)) {
        dVar12 = local_47c;
      }
      dVar11 = local_40c;
      if (local_40c <= dVar12) {
        dVar4 = local_4b4;
        if (local_4b4 < local_47c) {
          dVar4 = local_47c;
        }
        dVar11 = local_444;
        if ((local_444 <= dVar4) && (dVar11 = local_4b4, local_4b4 < local_47c)) {
          dVar11 = local_47c;
        }
      }
    }
    if (local_39c <= dVar11) {
      dVar4 = local_4b4;
      if (local_4b4 < local_47c) {
        dVar4 = local_47c;
      }
      dVar11 = local_444;
      if ((local_444 <= dVar4) && (dVar11 = local_4b4, local_4b4 < local_47c)) {
        dVar11 = local_47c;
      }
      dVar4 = local_40c;
      if (local_40c <= dVar11) {
        dVar11 = local_4b4;
        if (local_4b4 < local_47c) {
          dVar11 = local_47c;
        }
        dVar4 = local_444;
        if ((local_444 <= dVar11) && (dVar4 = local_4b4, local_4b4 < local_47c)) {
          dVar4 = local_47c;
        }
      }
      local_39c = local_3d4;
      if (local_3d4 <= dVar4) {
        dVar4 = local_4b4;
        if (local_4b4 < local_47c) {
          dVar4 = local_47c;
        }
        dVar11 = local_444;
        if ((local_444 <= dVar4) && (dVar11 = local_4b4, local_4b4 < local_47c)) {
          dVar11 = local_47c;
        }
        local_39c = local_40c;
        if (local_40c <= dVar11) {
          dVar4 = local_4b4;
          if (local_4b4 < local_47c) {
            dVar4 = local_47c;
          }
          local_39c = local_444;
          if ((local_444 <= dVar4) && (local_39c = local_4b4, local_4b4 < local_47c)) {
            local_39c = local_47c;
          }
        }
      }
    }
    local_5b4 = local_6fc;
    if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
      local_5b4 = dVar8;
    }
    local_5b4 = _DAT_10038470 - local_5b4;
    if (local_5b4 <= _DAT_10038470 - local_6f4) {
      local_5c4 = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_5c4 = dVar8;
      }
      local_5c4 = _DAT_10038470 - local_5c4;
      local_5bc = local_5c4;
    }
    else {
      local_5bc = _DAT_10038470 - local_6f4;
    }
    local_5e4 = dVar9;
    if (local_5bc <= dVar9) {
      local_5d4 = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_5d4 = dVar8;
      }
      local_5d4 = _DAT_10038470 - local_5d4;
      if (local_5d4 <= _DAT_10038470 - local_6f4) {
        local_5e4 = local_6fc;
        if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
          local_5e4 = dVar8;
        }
        local_5e4 = _DAT_10038470 - local_5e4;
      }
      else {
        local_5e4 = _DAT_10038470 - local_6f4;
      }
    }
    local_5ec = local_6fc;
    if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
      local_5ec = dVar8;
    }
    local_5ec = _DAT_10038470 - local_5ec;
    if (local_5ec <= _DAT_10038470 - dVar9) {
      local_5fc = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_5fc = dVar8;
      }
      local_5fc = _DAT_10038470 - local_5fc;
      local_5f4 = local_5fc;
    }
    else {
      local_5f4 = _DAT_10038470 - dVar9;
    }
    local_61c = local_6f4;
    if (local_5f4 <= local_6f4) {
      local_60c = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_60c = dVar8;
      }
      local_60c = _DAT_10038470 - local_60c;
      if (local_60c <= _DAT_10038470 - dVar9) {
        local_61c = local_6fc;
        if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
          local_61c = dVar8;
        }
        local_61c = _DAT_10038470 - local_61c;
      }
      else {
        local_61c = _DAT_10038470 - dVar9;
      }
    }
    local_624 = local_6fc;
    if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
      local_624 = local_6f4;
    }
    local_624 = _DAT_10038470 - local_624;
    if (local_624 <= _DAT_10038470 - dVar9) {
      local_634 = local_6fc;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
        local_634 = local_6f4;
      }
      local_634 = _DAT_10038470 - local_634;
      local_62c = local_634;
    }
    else {
      local_62c = _DAT_10038470 - dVar9;
    }
    local_654 = dVar8;
    if (local_62c <= dVar8) {
      local_644 = local_6fc;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
        local_644 = local_6f4;
      }
      local_644 = _DAT_10038470 - local_644;
      if (local_644 <= _DAT_10038470 - dVar9) {
        local_654 = local_6fc;
        if (_DAT_10038470 - local_6f4 < _DAT_10038470 - local_6fc) {
          local_654 = local_6f4;
        }
        local_654 = _DAT_10038470 - local_654;
      }
      else {
        local_654 = _DAT_10038470 - dVar9;
      }
    }
    local_65c = dVar8;
    if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
      local_65c = local_6f4;
    }
    local_65c = _DAT_10038470 - local_65c;
    if (local_65c <= _DAT_10038470 - dVar9) {
      local_66c = dVar8;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
        local_66c = local_6f4;
      }
      local_66c = _DAT_10038470 - local_66c;
      local_664 = local_66c;
    }
    else {
      local_664 = _DAT_10038470 - dVar9;
    }
    local_68c = local_6fc;
    if (local_664 <= local_6fc) {
      local_67c = dVar8;
      if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
        local_67c = local_6f4;
      }
      local_67c = _DAT_10038470 - local_67c;
      if (local_67c <= _DAT_10038470 - dVar9) {
        local_68c = dVar8;
        if (_DAT_10038470 - local_6f4 < _DAT_10038470 - dVar8) {
          local_68c = local_6f4;
        }
        local_68c = _DAT_10038470 - local_68c;
      }
      else {
        local_68c = _DAT_10038470 - dVar9;
      }
    }
    dVar4 = local_68c;
    if (local_68c < local_654) {
      dVar4 = local_654;
    }
    dVar11 = local_61c;
    if ((local_61c <= dVar4) && (dVar11 = local_68c, local_68c < local_654)) {
      dVar11 = local_654;
    }
    if (local_5e4 <= dVar11) {
      dVar4 = local_68c;
      if (local_68c < local_654) {
        dVar4 = local_654;
      }
      local_5e4 = local_61c;
      if ((local_61c <= dVar4) && (local_5e4 = local_68c, local_68c < local_654)) {
        local_5e4 = local_654;
      }
    }
    local_6cc = local_6fc;
    if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
      local_6cc = dVar8;
    }
    local_6cc = _DAT_10038470 - local_6cc;
    if (local_6cc <= _DAT_10038470 - local_6f4) {
      local_6dc = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_6dc = dVar8;
      }
      local_6dc = _DAT_10038470 - local_6dc;
      local_6d4 = local_6dc;
    }
    else {
      local_6d4 = _DAT_10038470 - local_6f4;
    }
    if (local_6d4 <= _DAT_10038470 - dVar9) {
      local_6ec = local_6fc;
      if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
        local_6ec = dVar8;
      }
      local_6ec = _DAT_10038470 - local_6ec;
      if (local_6ec <= _DAT_10038470 - local_6f4) {
        if (_DAT_10038470 - dVar8 < _DAT_10038470 - local_6fc) {
          local_6fc = dVar8;
        }
        local_6fc = _DAT_10038470 - local_6fc;
        local_6f4 = local_6fc;
      }
      else {
        local_6f4 = _DAT_10038470 - local_6f4;
      }
      local_6e4 = local_6f4;
    }
    else {
      local_6e4 = _DAT_10038470 - dVar9;
    }
    dVar4 = dVar3;
    if (dVar3 < dVar2) {
      dVar4 = dVar2;
    }
    dVar8 = local_6e4;
    if (local_6e4 < local_5e4) {
      dVar8 = local_5e4;
    }
    dVar11 = dVar6;
    if ((dVar6 <= dVar8) && (dVar11 = local_6e4, local_6e4 < local_5e4)) {
      dVar11 = local_5e4;
    }
    if (dVar11 <= dVar4) {
      dVar4 = local_6e4;
      if (local_6e4 < local_5e4) {
        dVar4 = local_5e4;
      }
      dVar8 = dVar6;
      if ((dVar6 <= dVar4) && (dVar8 = local_6e4, local_6e4 < local_5e4)) {
        dVar8 = local_5e4;
      }
      local_73c = SUB84(dVar8,0);
      local_72c = local_73c;
    }
    else {
      if (dVar2 <= dVar3) {
        local_724 = local_84;
      }
      else {
        local_724 = local_100;
      }
      local_72c = local_724;
    }
    (*(code *)puVar31[7])(puVar31,local_72c);
    dVar4 = dVar3;
    if (dVar3 < dVar2) {
      dVar4 = dVar2;
    }
    dVar8 = local_5e4;
    if (local_5e4 < local_39c) {
      dVar8 = local_39c;
    }
    if (_DAT_10038470 - dVar7 <= dVar8) {
      local_75c = local_5e4;
      if (local_5e4 < local_39c) {
        local_75c = local_39c;
      }
    }
    else {
      local_75c = _DAT_10038470 - dVar7;
    }
    if (local_75c <= dVar4) {
      dVar3 = local_5e4;
      if (local_5e4 < local_39c) {
        dVar3 = local_39c;
      }
      if (_DAT_10038470 - dVar7 <= dVar3) {
        if (local_5e4 < local_39c) {
          local_5e4 = local_39c;
        }
        local_784 = SUB84(local_5e4,0);
      }
      else {
        local_784 = SUB84(_DAT_10038470 - dVar7,0);
      }
      local_774 = local_784;
    }
    else {
      if (dVar2 <= dVar3) {
        local_76c = local_84;
      }
      else {
        local_76c = local_100;
      }
      local_774 = local_76c;
    }
    (*(code *)puVar32[7])(puVar32,local_774);
    local_794 = dVar7;
    if (_DAT_10038470 - dVar7 < _DAT_10038470 - dVar9) {
      local_794 = dVar9;
    }
    local_794 = _DAT_10038470 - local_794;
    local_79c = local_39c;
    if (local_39c < local_794) {
      local_79c = dVar7;
      if (_DAT_10038470 - dVar7 < _DAT_10038470 - dVar9) {
        local_79c = dVar9;
      }
      local_79c = _DAT_10038470 - local_79c;
    }
    if (local_79c <= dVar10) {
      local_7b4 = dVar7;
      if (_DAT_10038470 - dVar7 < _DAT_10038470 - dVar9) {
        local_7b4 = dVar9;
      }
      local_7b4 = _DAT_10038470 - local_7b4;
      local_7bc = local_39c;
      if (local_39c < local_7b4) {
        local_7bc = dVar7;
        if (_DAT_10038470 - dVar7 < _DAT_10038470 - dVar9) {
          local_7bc = dVar9;
        }
        local_7bc = _DAT_10038470 - local_7bc;
      }
      local_7c4 = SUB84(local_7bc,0);
      local_7ac = local_7c4;
    }
    else {
      local_7ac = local_18c;
    }
    (*(code *)puVar33[7])(puVar33,local_7ac);
    dVar3 = local_39c;
    if (dVar7 < local_39c) {
      dVar3 = dVar7;
    }
    dVar4 = dVar9;
    if ((dVar3 <= dVar9) && (dVar4 = local_39c, dVar7 < local_39c)) {
      dVar4 = dVar7;
    }
    dVar3 = dVar10;
    if (dVar4 <= dVar10) {
      dVar4 = local_39c;
      if (dVar7 < local_39c) {
        dVar4 = dVar7;
      }
      dVar3 = dVar9;
      if ((dVar4 <= dVar9) && (dVar3 = local_39c, dVar7 < local_39c)) {
        dVar3 = dVar7;
      }
    }
    local_7e4 = SUB84(dVar3,0);
    local_804 = dVar1;
    if (_DAT_10038470 - dVar6 < dVar1) {
      local_804 = _DAT_10038470 - dVar6;
    }
    dVar4 = dVar2;
    if ((local_804 <= dVar2) && (dVar4 = dVar1, _DAT_10038470 - dVar6 < dVar1)) {
      dVar4 = _DAT_10038470 - dVar6;
    }
    dVar8 = local_19c;
    if (local_19c <= dVar4) {
      local_824 = dVar1;
      if (_DAT_10038470 - dVar6 < dVar1) {
        local_824 = _DAT_10038470 - dVar6;
      }
      dVar8 = dVar2;
      if ((local_824 <= dVar2) && (dVar8 = dVar1, _DAT_10038470 - dVar6 < dVar1)) {
        dVar8 = _DAT_10038470 - dVar6;
      }
    }
    if (dVar3 <= dVar8) {
      local_844 = dVar1;
      if (_DAT_10038470 - dVar6 < dVar1) {
        local_844 = _DAT_10038470 - dVar6;
      }
      dVar3 = dVar2;
      if ((local_844 <= dVar2) && (dVar3 = dVar1, _DAT_10038470 - dVar6 < dVar1)) {
        dVar3 = _DAT_10038470 - dVar6;
      }
      if (local_19c <= dVar3) {
        local_864 = dVar1;
        if (_DAT_10038470 - dVar6 < dVar1) {
          local_864 = _DAT_10038470 - dVar6;
        }
        if (local_864 <= dVar2) {
          if (dVar1 <= _DAT_10038470 - dVar6) {
            local_874 = SUB84(dVar1,0);
          }
          else {
            local_874 = SUB84(_DAT_10038470 - dVar6,0);
          }
          local_86c = local_874;
        }
        else {
          local_86c = local_100;
        }
        local_19c = (double)(ulonglong)local_86c;
      }
      local_85c = SUB84(local_19c,0);
      local_83c = local_85c;
    }
    else {
      local_83c = local_7e4;
    }
    (*(code *)puVar34[7])(puVar34,local_83c);
    local_5c = SUB84(dVar7,0);
    dVar2 = dVar5;
    if (dVar7 < dVar5) {
      dVar2 = dVar7;
    }
    dVar3 = dVar10;
    if ((dVar2 <= dVar10) && (dVar3 = dVar5, dVar7 < dVar5)) {
      dVar3 = dVar7;
    }
    if (dVar3 <= dVar9) {
      dVar2 = dVar5;
      if (dVar7 < dVar5) {
        dVar2 = dVar7;
      }
      if (dVar2 <= dVar10) {
        if (dVar5 <= dVar7) {
          local_8ac = local_34c;
        }
        else {
          local_8ac = local_5c;
        }
        local_8a4 = local_8ac;
      }
      else {
        local_8a4 = local_18c;
      }
      local_894 = local_8a4;
    }
    else {
      local_894 = local_f4;
    }
    (*(code *)puVar35[7])(puVar35,local_894);
    dVar2 = dVar1;
    if (dVar7 < dVar1) {
      dVar2 = dVar7;
    }
    if (dVar2 <= dVar10) {
      if (dVar7 < dVar1) {
        dVar1 = dVar7;
      }
      local_8c4 = SUB84(dVar1,0);
      local_8bc = local_8c4;
    }
    else {
      local_8bc = local_18c;
    }
    (*(code *)puVar36[7])(puVar36,local_8bc);
    (*(code *)puVar27[1])(puVar27,puVar28);
    (*(code *)puVar27[1])(puVar27,puVar29);
    (*(code *)puVar27[1])(puVar27,puVar30);
    (*(code *)puVar27[1])(puVar27,puVar31);
    (*(code *)puVar27[1])(puVar27,puVar32);
    (*(code *)puVar27[1])(puVar27,puVar33);
    (*(code *)puVar27[1])(puVar27,puVar34);
    (*(code *)puVar27[1])(puVar27,puVar35);
    (*(code *)puVar27[1])(puVar27,puVar36);
    (*(code *)*puVar27)(puVar27);
    cVar14 = BandStatArray::call((BandStatArray *)(this + 0x1c),local_8);
    if ((cVar14 == '-') ||
       (cVar14 = BandStatArray::call((BandStatArray *)(this + 0x1c),local_8), cVar14 == 'N')) {
      BandStatArray::qual((BandStatArray *)(this + 0x1c),local_8,0.5);
    }
    else {
      BandStatArray::qual((BandStatArray *)(this + 0x1c),local_8,(float)local_148);
    }
    FUN_10013a38(puVar27);
    FUN_10013a38(puVar28);
    FUN_10013a38(puVar29);
    FUN_10013a38(puVar30);
    FUN_10013a38(puVar31);
    FUN_10013a38(puVar32);
    FUN_10013a38(puVar33);
    FUN_10013a38(puVar34);
    FUN_10013a38(puVar35);
    FUN_10013a38(puVar36);
  }
  FUN_10013a38(puVar16);
  FUN_10013a38(puVar17);
  FUN_10013a38(puVar18);
  FUN_10013a38(puVar19);
  FUN_10013a38(puVar20);
  FUN_10013a38(puVar21);
  FUN_10013a38(puVar22);
  FUN_10013a38(puVar23);
  FUN_10013a38(puVar24);
  FUN_10013a38(puVar25);
  FUN_10013a38(puVar26);
  return;
}

//===== 0x100092b7 =====

void FUN_100092b7(void)

{
  FUN_100092c1();
  return;
}

//===== 0x100092c1 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_100092c1(void)

{
  _DAT_10041af8 = acos(-1.0);
  return;
}

//===== 0x100092e0 =====

undefined4 * __thiscall FUN_100092e0(void *this,Wvfm *param_1,uint *param_2)

{
  int iVar1;
  double *pdVar2;
  int *piVar3;
  void *pvVar4;
  int local_8;
  
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  iVar1 = Wvfm::bgni(param_1);
  *(int *)((int)this + 0xc) = iVar1;
  iVar1 = Wvfm::endi(param_1);
  *(int *)((int)this + 0x10) = iVar1;
  *(undefined4 *)((int)this + 0x14) = 1;
  iVar1 = Wvfm::endi(param_1);
  *(int *)((int)this + 0x18) = iVar1;
  *(undefined4 *)((int)this + 0x1c) = 0;
  *(undefined4 *)((int)this + 0x20) = 0;
  *(undefined4 *)((int)this + 0x24) = 0;
  *(undefined4 *)((int)this + 0x28) = 0;
  *(undefined4 *)((int)this + 0x2c) = 0;
  *(undefined4 *)((int)this + 0x30) = 0;
  *(undefined4 *)((int)this + 0x34) = 0x32;
  iVar1 = Wvfm::rows(param_1);
  *(int *)((int)this + 0x368) = iVar1;
  *(undefined4 *)((int)this + 0x36c) = 0;
  *(undefined4 *)((int)this + 0x370) = 0;
  *(undefined4 *)((int)this + 0x374) = 0;
  pdVar2 = dvector(1,*(long *)((int)this + 0x368));
  *(double **)((int)this + 0x20) = pdVar2;
  piVar3 = ivector(1,*(long *)((int)this + 0x368));
  *(int **)((int)this + 0x24) = piVar3;
  if ((*(int *)((int)this + 0x20) == 0) || (*(int *)((int)this + 0x24) == 0)) {
    FUN_10009637((int)this);
    *(undefined4 *)this = 1;
  }
  else {
    if ((*param_2 & 1) == 1) {
      for (local_8 = 1; local_8 < 5; local_8 = local_8 + 1) {
        FUN_10009a67(this,local_8,param_1,(uint)((*param_2 >> 4 & 1) == 1));
      }
      *(undefined4 *)((int)this + 0x14) = *(undefined4 *)((int)this + 0xc);
      *(undefined4 *)((int)this + 0x18) = *(undefined4 *)((int)this + 0x10);
    }
    else {
      *(int *)((int)this + 0x28) = *(int *)((int)this + 0x368) / 200;
      pvVar4 = operator_new(*(int *)((int)this + 0x28) * 4 + 4);
      *(void **)((int)this + 0x30) = pvVar4;
      pvVar4 = operator_new(*(int *)((int)this + 0x28) * 4 + 4);
      *(void **)((int)this + 0x2c) = pvVar4;
      for (local_8 = 0; local_8 <= *(int *)((int)this + 0x28); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)((int)this + 0x30) + local_8 * 4) = 0;
        *(int *)(*(int *)((int)this + 0x2c) + local_8 * 4) =
             (*(int *)((int)this + 0x368) * (local_8 * 2 + 1)) / (*(int *)((int)this + 0x28) << 1);
      }
      FUN_1000a040(this,param_1);
      FUN_1000a17b((int)this);
      FUN_1000a24e((int)this);
      FUN_1000a3b8((int)this);
      for (local_8 = 0; local_8 <= *(int *)((int)this + 0x34); local_8 = local_8 + 1) {
        *(undefined4 *)((int)this + local_8 * 4 + 0x29c) = 0;
        *(undefined4 *)((int)this + local_8 * 4 + 0x1d0) = 0;
        *(undefined4 *)((int)this + local_8 * 4 + 0x38) = 0;
        *(undefined4 *)((int)this + local_8 * 4 + 0x104) = 0;
      }
      FUN_1000a61f(this);
      FUN_1000ab7e((int)this);
      FUN_1000ac91((int)this);
    }
    FUN_10009637((int)this);
    *(undefined4 *)this = 2;
    if (*(int *)((int)this + 0x18) - *(int *)((int)this + 0x14) < 0x801) {
      if (*(int *)((int)this + 0x368) < *(int *)((int)this + 0x14) + 0x801) {
        *(undefined4 *)((int)this + 0x18) = *(undefined4 *)((int)this + 0x368);
      }
      else {
        *(int *)((int)this + 0x18) = *(int *)((int)this + 0x14) + 0x801;
      }
    }
  }
  return this;
}

//===== 0x10009624 =====

void __fastcall FUN_10009624(int param_1)

{
  FUN_10009637(param_1);
  return;
}

//===== 0x10009637 =====

void __fastcall FUN_10009637(int param_1)

{
  if (*(int *)(param_1 + 0x20) != 0) {
    free_dvector(*(double **)(param_1 + 0x20),1,*(long *)(param_1 + 0x368));
    *(undefined4 *)(param_1 + 0x20) = 0;
  }
  if (*(int *)(param_1 + 0x24) != 0) {
    free_ivector(*(int **)(param_1 + 0x24),1,*(long *)(param_1 + 0x368));
    *(undefined4 *)(param_1 + 0x24) = 0;
  }
  if (*(int *)(param_1 + 0x30) != 0) {
    operator_delete(*(void **)(param_1 + 0x30));
    *(undefined4 *)(param_1 + 0x30) = 0;
  }
  if (*(int *)(param_1 + 0x2c) != 0) {
    operator_delete(*(void **)(param_1 + 0x2c));
    *(undefined4 *)(param_1 + 0x2c) = 0;
  }
  return;
}

//===== 0x100096f0 =====

undefined4 * __thiscall FUN_100096f0(void *this,undefined4 *param_1)

{
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0xc) = 0;
  *(undefined4 *)((int)this + 0x10) = 0;
  *(undefined4 *)((int)this + 0x14) = 0;
  *(undefined4 *)((int)this + 0x18) = 0;
  *(undefined4 *)((int)this + 0x1c) = 0;
  *(undefined4 *)((int)this + 0x20) = 0;
  *(undefined4 *)((int)this + 0x24) = 0;
  *(undefined4 *)((int)this + 0x28) = 0;
  *(undefined4 *)((int)this + 0x2c) = 0;
  *(undefined4 *)((int)this + 0x30) = 0;
  *(undefined4 *)((int)this + 0x368) = 0;
  *(undefined4 *)((int)this + 0x36c) = 0;
  *(undefined4 *)((int)this + 0x370) = 0;
  *(undefined4 *)((int)this + 0x374) = 0;
  FUN_100097be(this,param_1);
  return this;
}

//===== 0x100097be =====

undefined4 * __thiscall FUN_100097be(void *this,undefined4 *param_1)

{
  int iVar1;
  int iVar2;
  double *pdVar3;
  int *piVar4;
  void *pvVar5;
  int local_8;
  
  if (param_1 != this) {
    FUN_10009637((int)this);
    *(undefined4 *)this = *param_1;
    *(undefined4 *)((int)this + 4) = param_1[1];
    *(undefined4 *)((int)this + 8) = param_1[2];
    *(undefined4 *)((int)this + 0xc) = param_1[3];
    *(undefined4 *)((int)this + 0x10) = param_1[4];
    *(undefined4 *)((int)this + 0x14) = param_1[5];
    *(undefined4 *)((int)this + 0x18) = param_1[6];
    *(undefined4 *)((int)this + 0x368) = param_1[0xda];
    *(undefined4 *)((int)this + 0x36c) = param_1[0xdb];
    *(undefined4 *)((int)this + 0x370) = param_1[0xdc];
    *(undefined4 *)((int)this + 0x374) = param_1[0xdd];
    *(undefined4 *)((int)this + 0x1c) = param_1[7];
    *(undefined4 *)((int)this + 0x34) = param_1[0xd];
    if (param_1[8] != 0) {
      pdVar3 = dvector(1,*(long *)((int)this + 0x368));
      *(double **)((int)this + 0x20) = pdVar3;
      piVar4 = ivector(1,*(long *)((int)this + 0x368));
      *(int **)((int)this + 0x24) = piVar4;
      for (local_8 = 1; local_8 <= *(int *)((int)this + 0x368); local_8 = local_8 + 1) {
        iVar1 = param_1[8];
        iVar2 = *(int *)((int)this + 0x20);
        *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
        *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
        *(undefined4 *)(*(int *)((int)this + 0x24) + local_8 * 4) =
             *(undefined4 *)(param_1[9] + local_8 * 4);
      }
    }
    *(undefined4 *)((int)this + 0x28) = param_1[10];
    pvVar5 = operator_new(*(int *)((int)this + 0x28) * 4 + 4);
    *(void **)((int)this + 0x30) = pvVar5;
    pvVar5 = operator_new(*(int *)((int)this + 0x28) * 4 + 4);
    *(void **)((int)this + 0x2c) = pvVar5;
    for (local_8 = 0; local_8 < *(int *)((int)this + 0x28); local_8 = local_8 + 1) {
      *(undefined4 *)(*(int *)((int)this + 0x30) + local_8 * 4) =
           *(undefined4 *)(param_1[0xc] + local_8 * 4);
      *(undefined4 *)(*(int *)((int)this + 0x2c) + local_8 * 4) =
           *(undefined4 *)(param_1[0xb] + local_8 * 4);
    }
    for (local_8 = 0; local_8 < *(int *)((int)this + 0x34); local_8 = local_8 + 1) {
      *(undefined4 *)((int)this + local_8 * 4 + 0x104) = param_1[local_8 + 0x41];
      *(undefined4 *)((int)this + local_8 * 4 + 0x38) = param_1[local_8 + 0xe];
      *(undefined4 *)((int)this + local_8 * 4 + 0x1d0) = param_1[local_8 + 0x74];
      *(undefined4 *)((int)this + local_8 * 4 + 0x29c) = param_1[local_8 + 0xa7];
    }
  }
  return this;
}

//===== 0x10009a43 =====

void FUN_10009a43(void)

{
  FUN_10009a4d();
  return;
}

//===== 0x10009a4d =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10009a4d(void)

{
  _DAT_10041b60 = acos(-1.0);
  return;
}

//===== 0x10009a67 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __thiscall FUN_10009a67(void *this,int param_1,Wvfm *param_2,int param_3)

{
  int iVar1;
  int iVar2;
  bool bVar3;
  int iVar4;
  int iVar5;
  float10 fVar6;
  double dVar7;
  int local_58;
  int local_50;
  int local_4c;
  undefined8 local_48;
  int local_38;
  int local_28;
  int local_24;
  int local_20;
  int local_1c;
  int local_18;
  undefined4 local_c;
  undefined4 uStack_8;
  
  iVar4 = *(int *)((int)this + 0x368) / 200;
  local_18 = 1;
  bVar3 = false;
  local_1c = 0;
  local_28 = 0;
  local_24 = 0;
  Wvfm::sc_la(param_2,1,param_1);
  local_c = 0;
  uStack_8 = 0;
  for (local_38 = 1; local_38 <= *(int *)((int)this + 0x368); local_38 = local_38 + 1) {
    dVar7 = Wvfm::sc_la(param_2,local_38,param_1);
    *(double *)(*(int *)((int)this + 0x20) + local_38 * 8) = dVar7;
  }
  local_20 = iVar4;
  for (local_50 = 1; local_50 <= iVar4; local_50 = local_50 + 1) {
    local_38 = (local_50 + -1) * 200;
    iVar5 = local_38 + 1;
    iVar1 = local_38 + 200;
    local_48 = (double)CONCAT44(*(undefined4 *)(*(int *)((int)this + 0x20) + 4 + iVar5 * 8),
                                *(undefined4 *)(*(int *)((int)this + 0x20) + iVar5 * 8));
    for (local_38 = local_38 + 2; iVar2 = iVar5, local_38 <= iVar1; local_38 = local_38 + 1) {
      if (*(double *)(*(int *)((int)this + 0x20) + local_38 * 8) < local_48) {
        local_48 = (double)CONCAT44(*(undefined4 *)(*(int *)((int)this + 0x20) + 4 + local_38 * 8),
                                    *(undefined4 *)(*(int *)((int)this + 0x20) + local_38 * 8));
      }
    }
    while (local_38 = iVar2, local_38 <= iVar1) {
      *(double *)(*(int *)((int)this + 0x20) + local_38 * 8) =
           *(double *)(*(int *)((int)this + 0x20) + local_38 * 8) - local_48;
      if (_DAT_10038480 < *(double *)(*(int *)((int)this + 0x20) + local_38 * 8)) {
        iVar2 = *(int *)((int)this + 0x20);
        *(undefined4 *)(iVar2 + local_38 * 8) = 0;
        *(undefined4 *)(iVar2 + 4 + local_38 * 8) = 0x40b77000;
      }
      if ((double)CONCAT44(uStack_8,local_c) <
          *(double *)(*(int *)((int)this + 0x20) + local_38 * 8)) {
        local_c = *(undefined4 *)(*(int *)((int)this + 0x20) + local_38 * 8);
        uStack_8 = *(undefined4 *)(*(int *)((int)this + 0x20) + 4 + local_38 * 8);
      }
      iVar2 = local_38 + 1;
    }
    fVar6 = FUN_10009fa0(*(int *)((int)this + 0x20),iVar5,iVar1);
    if (bVar3) {
      local_28 = local_50;
      if (_DAT_10038488 <= (double)fVar6) {
        if (0 < local_24) {
          local_24 = local_24 + -1;
        }
      }
      else {
        local_24 = local_24 + 1;
        if (2 < local_24) {
          bVar3 = false;
          local_28 = local_50 - local_24;
          local_24 = 0;
          local_28 = local_28 + -1;
          if (local_18 - local_20 < local_28 - local_1c) {
            local_20 = local_1c;
            local_18 = local_28;
          }
        }
      }
    }
    else if ((double)fVar6 < _DAT_10038488) {
      if (0 < local_24) {
        local_24 = local_24 + -1;
      }
    }
    else {
      local_24 = local_24 + 1;
      if (2 < local_24) {
        local_28 = (local_50 - local_24) + 1;
        bVar3 = true;
        local_24 = 0;
        local_1c = local_28;
      }
    }
  }
  if ((bVar3) && (local_18 - local_20 < (local_28 - local_24) - local_1c)) {
    local_20 = local_1c;
    local_18 = local_28 - local_24;
  }
  iVar4 = (local_20 + -1) * 200;
  local_4c = iVar4 + 1;
  local_58 = local_18 * 200;
  if (((param_3 != 0) && (199 < local_4c)) &&
     (fVar6 = FUN_10009fa0(*(int *)((int)this + 0x20),iVar4 + -99,iVar4 + 100),
     (double)fVar6 < _DAT_10038488)) {
    local_4c = iVar4 + 0x65;
  }
  dVar7 = (double)CONCAT44(uStack_8,local_c) / _DAT_10038490;
  iVar4 = local_4c + 200;
  if ((param_1 == 1) || (local_4c < *(int *)((int)this + 0xc))) {
    for (; local_4c < iVar4; local_4c = local_4c + 1) {
      if (dVar7 <= *(double *)(*(int *)((int)this + 0x20) + local_4c * 8)) goto LAB_10009e2b;
    }
  }
  goto LAB_10009e97;
  while (dVar7 <= *(double *)(*(int *)((int)this + 0x20) + local_58 * 8)) {
LAB_10009eeb:
    local_58 = local_58 + -1;
    if (local_58 <= iVar4) break;
  }
  for (; (iVar4 < local_58 &&
         (*(double *)(*(int *)((int)this + 0x20) + local_58 * 8) <
          *(double *)(*(int *)((int)this + 0x20) + 8 + local_58 * 8))); local_58 = local_58 + -1) {
  }
  local_58 = local_58 + 1;
  goto LAB_10009f57;
  while (dVar7 <= *(double *)(*(int *)((int)this + 0x20) + local_4c * 8)) {
LAB_10009e2b:
    local_4c = local_4c + 1;
    if (iVar4 <= local_4c) break;
  }
  for (; (local_4c < iVar4 &&
         (*(double *)(*(int *)((int)this + 0x20) + local_4c * 8) <
          *(double *)(*(int *)((int)this + 0x20) + -8 + local_4c * 8))); local_4c = local_4c + 1) {
  }
  local_4c = local_4c + -1;
LAB_10009e97:
  iVar4 = local_58 + -200;
  if ((param_1 == 1) || (*(int *)((int)this + 0x10) < local_58)) {
    for (; iVar4 < local_58; local_58 = local_58 + -1) {
      if (dVar7 <= *(double *)(*(int *)((int)this + 0x20) + local_58 * 8)) goto LAB_10009eeb;
    }
  }
LAB_10009f57:
  if (param_1 == 1) {
    *(int *)((int)this + 0xc) = local_4c;
    *(int *)((int)this + 0x10) = local_58;
  }
  else {
    if (local_4c < *(int *)((int)this + 0xc)) {
      *(int *)((int)this + 0xc) = local_4c;
    }
    if (*(int *)((int)this + 0x10) < local_58) {
      *(int *)((int)this + 0x10) = local_58;
    }
  }
  return;
}

//===== 0x10009fa0 =====

float10 __cdecl FUN_10009fa0(int param_1,int param_2,int param_3)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  double dVar4;
  undefined8 local_1c;
  undefined4 local_10;
  undefined8 local_c;
  
  local_1c = 0.0;
  local_c = 0.0;
  iVar3 = (param_3 - param_2) + 1;
  for (local_10 = param_2; local_10 <= param_3; local_10 = local_10 + 1) {
    uVar1 = *(undefined4 *)(param_1 + local_10 * 8);
    uVar2 = *(undefined4 *)(param_1 + 4 + local_10 * 8);
    local_1c = local_1c + (double)CONCAT44(uVar2,uVar1);
    local_c = (double)CONCAT44(uVar2,uVar1) * (double)CONCAT44(uVar2,uVar1) + local_c;
  }
  local_1c = local_1c / (double)iVar3;
  dVar4 = sqrt(local_c / (double)iVar3 - local_1c * local_1c);
  return (float10)dVar4 / (float10)local_1c;
}

//===== 0x1000a040 =====

void __thiscall FUN_1000a040(void *this,Wvfm *param_1)

{
  int iVar1;
  double dVar2;
  undefined4 local_3c;
  undefined4 uStack_38;
  int local_34;
  double adStack_30 [5];
  int local_8;
  
  for (local_34 = 1; local_34 < 5; local_34 = local_34 + 1) {
    dVar2 = Wvfm::sc_la(param_1,1,local_34);
    adStack_30[local_34] = dVar2;
    for (local_8 = 2; local_8 <= *(int *)((int)this + 0x368); local_8 = local_8 + 1) {
      dVar2 = Wvfm::sc_la(param_1,local_8,local_34);
      if (dVar2 < adStack_30[local_34]) {
        dVar2 = Wvfm::sc_la(param_1,local_8,local_34);
        adStack_30[local_34] = dVar2;
      }
    }
  }
  for (local_8 = 1; local_8 <= *(int *)((int)this + 0x368); local_8 = local_8 + 1) {
    dVar2 = Wvfm::sc_la(param_1,local_8,1);
    *(double *)(*(int *)((int)this + 0x20) + local_8 * 8) = dVar2 - adStack_30[1];
    for (local_34 = 2; local_34 < 5; local_34 = local_34 + 1) {
      dVar2 = Wvfm::sc_la(param_1,local_8,local_34);
      dVar2 = dVar2 - adStack_30[local_34];
      if (*(double *)(*(int *)((int)this + 0x20) + local_8 * 8) < dVar2) {
        iVar1 = *(int *)((int)this + 0x20);
        local_3c = SUB84(dVar2,0);
        *(undefined4 *)(iVar1 + local_8 * 8) = local_3c;
        uStack_38 = (undefined4)((ulonglong)dVar2 >> 0x20);
        *(undefined4 *)(iVar1 + 4 + local_8 * 8) = uStack_38;
      }
    }
  }
  return;
}

//===== 0x1000a17b =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_1000a17b(int param_1)

{
  double dVar1;
  bool bVar2;
  int iVar3;
  int local_8;
  
  bVar2 = true;
  *(undefined4 *)(param_1 + 0x36c) = 0;
  iVar3 = *(int *)(param_1 + 0xc);
  while (local_8 = iVar3 + 1, local_8 < *(int *)(param_1 + 0x10)) {
    dVar1 = *(double *)(*(int *)(param_1 + 0x20) + local_8 * 8) -
            *(double *)(*(int *)(param_1 + 0x20) + -8 + local_8 * 8);
    if ((bVar2) || (_DAT_10038498 <= dVar1)) {
      iVar3 = local_8;
      if ((bVar2) && (_DAT_10038498 < dVar1)) {
        bVar2 = false;
      }
    }
    else {
      bVar2 = true;
      *(int *)(param_1 + 0x36c) = *(int *)(param_1 + 0x36c) + 1;
      *(int *)(*(int *)(param_1 + 0x24) + *(int *)(param_1 + 0x36c) * 4) = iVar3;
      iVar3 = local_8;
    }
  }
  return;
}

//===== 0x1000a24e =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_1000a24e(int param_1)

{
  int iVar1;
  int iVar2;
  double dVar3;
  undefined4 local_8;
  
  for (local_8 = 1; local_8 <= *(int *)(param_1 + 0x36c); local_8 = local_8 + 1) {
    iVar1 = ftol();
    iVar1 = *(int *)(*(int *)(param_1 + 0x30) + iVar1 * 4);
    iVar2 = ftol();
    *(int *)(*(int *)(param_1 + 0x30) + iVar2 * 4) = iVar1 + 1;
  }
  *(undefined4 *)(param_1 + 4) = 0;
  for (local_8 = 0; local_8 < *(int *)(param_1 + 0x28); local_8 = local_8 + 1) {
    *(float *)(param_1 + 4) =
         (float)*(int *)(*(int *)(param_1 + 0x30) + local_8 * 4) + *(float *)(param_1 + 4);
    *(float *)(param_1 + 8) =
         (float)(*(int *)(*(int *)(param_1 + 0x30) + local_8 * 4) *
                *(int *)(*(int *)(param_1 + 0x30) + local_8 * 4)) + *(float *)(param_1 + 8);
  }
  *(float *)(param_1 + 4) = *(float *)(param_1 + 4) / (float)local_8;
  dVar3 = sqrt((double)(*(float *)(param_1 + 8) / (float)local_8 -
                       *(float *)(param_1 + 4) * *(float *)(param_1 + 4)));
  *(float *)(param_1 + 8) = (float)dVar3;
  return;
}

//===== 0x1000a3b8 =====

void __fastcall FUN_1000a3b8(int param_1)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  int local_30;
  int local_1c;
  int local_18;
  int local_10;
  int local_c;
  int local_8;
  
  bVar1 = false;
  local_1c = 0;
  local_10 = 0;
  local_18 = 0;
  for (local_8 = 0; local_8 < *(int *)(param_1 + 0x28); local_8 = local_8 + 1) {
    iVar3 = *(int *)(param_1 + 0x30);
    iVar2 = ftol();
    iVar2 = *(int *)(iVar3 + local_8 * 4) - iVar2;
    if (bVar1) {
      if (iVar2 < 1) {
        if (0 < local_1c) {
          local_1c = local_1c + -1;
        }
      }
      else {
        local_1c = local_1c + 1;
        if (2 < local_1c) {
          iVar3 = (local_8 - local_1c) + 1;
          bVar1 = false;
          local_1c = 0;
          if ((local_18 - local_10 < iVar3 - local_c) &&
             (local_10 = local_c, local_18 = iVar3,
             *(int *)(param_1 + 0x28) < ((local_8 + iVar3) - local_c) + 1)) break;
        }
      }
    }
    else if (iVar2 < 1) {
      local_1c = local_1c + 1;
      if (2 < local_1c) {
        local_c = (local_8 - local_1c) + 1;
        bVar1 = true;
        local_1c = 0;
      }
    }
    else if (0 < local_1c) {
      local_1c = local_1c + -1;
    }
  }
  if ((bVar1) && (iVar3 = *(int *)(param_1 + 0x28) + -1, local_18 - local_10 < iVar3 - local_c)) {
    local_10 = local_c;
    local_18 = iVar3;
  }
  if (local_10 < 1) {
    local_30 = *(int *)(*(int *)(param_1 + 0x2c) + local_10 * 4);
  }
  else {
    local_30 = *(int *)(*(int *)(param_1 + 0x2c) + -4 + local_10 * 4) +
               *(int *)(*(int *)(param_1 + 0x2c) + local_10 * 4);
  }
  local_30 = local_30 / 2;
  *(int *)(param_1 + 0xc) = local_30;
  *(undefined4 *)(param_1 + 0x10) = *(undefined4 *)(*(int *)(param_1 + 0x2c) + local_18 * 4);
  return;
}

//===== 0x1000a572 =====

void __thiscall FUN_1000a572(void *this,int param_1,double *param_2,double *param_3)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  
  iVar1 = *(int *)((int)this + 0x20);
  *(undefined4 *)param_2 = *(undefined4 *)(iVar1 + param_1 * 8);
  *(undefined4 *)((int)param_2 + 4) = *(undefined4 *)(iVar1 + 4 + param_1 * 8);
  *(undefined4 *)param_3 = *(undefined4 *)param_2;
  *(undefined4 *)((int)param_3 + 4) = *(undefined4 *)((int)param_2 + 4);
  while (param_1 = param_1 + 1, param_1 <= *(int *)((int)this + 0x368)) {
    uVar2 = *(undefined4 *)(*(int *)((int)this + 0x20) + param_1 * 8);
    uVar3 = *(undefined4 *)(*(int *)((int)this + 0x20) + 4 + param_1 * 8);
    if (*param_2 < (double)CONCAT44(uVar3,uVar2)) {
      *(undefined4 *)param_2 = uVar2;
      *(undefined4 *)((int)param_2 + 4) = uVar3;
    }
    if ((double)CONCAT44(uVar3,uVar2) < *param_3) {
      *(undefined4 *)param_3 = uVar2;
      *(undefined4 *)((int)param_3 + 4) = uVar3;
    }
  }
  return;
}

//===== 0x1000a61f =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_1000a61f(void *param_1)

{
  undefined4 uVar1;
  double local_48;
  int local_40;
  undefined4 local_34;
  undefined4 uStack_30;
  int local_2c;
  double local_28;
  int local_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  double local_14;
  int local_c;
  int local_8;
  
  local_c = 0;
  local_2c = 0;
  FUN_1000a866(*(int *)((int)param_1 + 0x20),*(int *)((int)param_1 + 0x368),
               (double *)((int)param_1 + 0x370),(int *)((int)param_1 + 0x1c));
  FUN_1000a572(param_1,*(int *)((int)param_1 + 0xc),&local_14,(double *)&local_34);
  while ((local_c < *(int *)((int)param_1 + 0x34) / 2 && (local_2c = local_2c + 1, local_2c < 4))) {
    local_48 = 0.0;
    local_40 = 0;
    local_28 = ((double)*(int *)((int)param_1 + 0x34) - _DAT_10038498) /
               ((local_14 - (double)CONCAT44(uStack_30,local_34)) + _DAT_100384a0);
    for (local_c = 0; local_c < *(int *)((int)param_1 + 0x34); local_c = local_c + 1) {
      *(undefined4 *)((int)param_1 + local_c * 4 + 0x104) = 0;
      uVar1 = ftol();
      *(undefined4 *)((int)param_1 + local_c * 4 + 0x38) = uVar1;
    }
    local_34 = *(undefined4 *)((int)param_1 + 0x370);
    uStack_30 = *(undefined4 *)((int)param_1 + 0x374);
    for (local_8 = *(int *)((int)param_1 + 0xc); local_8 <= *(int *)((int)param_1 + 0x368);
        local_8 = local_8 + 1) {
      local_1c = *(undefined4 *)(*(int *)((int)param_1 + 0x20) + local_8 * 8);
      uStack_18 = *(undefined4 *)(*(int *)((int)param_1 + 0x20) + 4 + local_8 * 8);
      if ((double)CONCAT44(uStack_18,local_1c) < (double)CONCAT44(uStack_30,local_34)) {
        local_34 = local_1c;
        uStack_30 = uStack_18;
      }
      local_20 = ftol();
      if ((-1 < local_20) && (local_20 < *(int *)((int)param_1 + 0x34))) {
        *(int *)((int)param_1 + local_20 * 4 + 0x104) =
             *(int *)((int)param_1 + local_20 * 4 + 0x104) + 1;
        local_40 = local_40 + 1;
      }
    }
    local_c = 0;
    while ((local_c < *(int *)((int)param_1 + 0x34) &&
           (local_48 = (double)*(int *)((int)param_1 + local_c * 4 + 0x104) / (double)local_40 +
                       local_48, local_48 < _DAT_100384a8))) {
      local_c = local_c + 1;
    }
    local_14 = (double)(*(int *)((int)param_1 + local_c * 4 + 0x38) +
                       (*(int *)((int)param_1 + 0x3c) - *(int *)((int)param_1 + 0x38)) / 2);
  }
  *(int *)((int)param_1 + 0x34) = local_c;
  if (local_c < 10) {
    *(undefined4 *)((int)param_1 + 0x34) = 10;
  }
  return;
}

//===== 0x1000a866 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_1000a866(int param_1,int param_2,double *param_3,int *param_4)

{
  float fVar1;
  int iVar2;
  void *pvVar3;
  int *piVar4;
  int iVar5;
  int local_28;
  float local_24;
  int local_20;
  int local_1c;
  float local_10;
  int local_c;
  
  iVar2 = param_2 / 100;
  pvVar3 = operator_new(iVar2 << 2);
  piVar4 = operator_new(iVar2 << 2);
  local_28 = 0x32;
  local_c = 1;
  for (local_20 = 0; local_20 < iVar2; local_20 = local_20 + 1) {
    *(int *)((int)pvVar3 + local_20 * 4) = local_28;
    iVar5 = ftol();
    piVar4[local_20] = iVar5;
    local_28 = local_28 + 100;
    for (local_1c = 1; local_c = local_c + 1, local_1c < 100; local_1c = local_1c + 1) {
      if (*(double *)(param_1 + local_c * 8) < (double)piVar4[local_20]) {
        iVar5 = ftol();
        piVar4[local_20] = iVar5;
      }
    }
  }
  *param_4 = 1;
  *(undefined4 *)param_3 = *(undefined4 *)(param_1 + 8);
  *(undefined4 *)((int)param_3 + 4) = *(undefined4 *)(param_1 + 0xc);
  local_24 = (float)(piVar4[1] - *piVar4) / _DAT_100384b0;
  local_10 = (float)piVar4[1] - (float)*(int *)((int)pvVar3 + 4) * local_24;
  local_c = 1;
  for (local_20 = 0; local_20 < iVar2; local_20 = local_20 + 1) {
    for (local_1c = 0; local_1c < 100; local_1c = local_1c + 1) {
      *(double *)(param_1 + local_c * 8) =
           (double)((float)*(double *)(param_1 + local_c * 8) -
                   ((float)local_c * local_24 + local_10));
      if (_DAT_10038498 <= *(double *)(param_1 + local_c * 8)) {
        if (*param_3 < *(double *)(param_1 + local_c * 8)) {
          *param_4 = local_c;
          *(undefined4 *)param_3 = *(undefined4 *)(param_1 + local_c * 8);
          *(undefined4 *)((int)param_3 + 4) = *(undefined4 *)(param_1 + 4 + local_c * 8);
        }
      }
      else {
        *(undefined4 *)(param_1 + local_c * 8) = 0;
        *(undefined4 *)(param_1 + 4 + local_c * 8) = 0;
      }
      local_c = local_c + 1;
    }
    if (local_20 < iVar2 + -1) {
      local_24 = (float)(piVar4[local_20 + 1] - piVar4[local_20]) / _DAT_100384b0;
      local_10 = (float)piVar4[local_20] - (float)*(int *)((int)pvVar3 + local_20 * 4) * local_24;
    }
  }
  fVar1 = (float)local_c;
  for (; local_c < param_2; local_c = local_c + 1) {
    *(double *)(param_1 + local_c * 8) =
         (double)((float)*(double *)(param_1 + local_c * 8) - (fVar1 * local_24 + local_10));
    if (_DAT_10038498 <= *(double *)(param_1 + local_c * 8)) {
      if (*param_3 < *(double *)(param_1 + local_c * 8)) {
        *param_4 = local_c;
        *(undefined4 *)param_3 = *(undefined4 *)(param_1 + local_c * 8);
        *(undefined4 *)((int)param_3 + 4) = *(undefined4 *)(param_1 + 4 + local_c * 8);
      }
    }
    else {
      *(undefined4 *)(param_1 + local_c * 8) = 0;
      *(undefined4 *)(param_1 + 4 + local_c * 8) = 0;
    }
  }
  operator_delete(pvVar3);
  operator_delete(piVar4);
  return;
}

//===== 0x1000ab7e =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_1000ab7e(int param_1)

{
  int local_14;
  float local_10;
  int local_c;
  float local_8;
  
  local_8 = 0.0;
  local_10 = 0.0;
  for (local_14 = 1; local_14 < *(int *)(param_1 + 0x34); local_14 = local_14 + 1) {
    local_8 = (float)*(int *)(param_1 + 0x104 + local_14 * 4) + local_8;
  }
  for (local_14 = 1; local_14 < *(int *)(param_1 + 0x34); local_14 = local_14 + 1) {
    local_c = local_14;
    local_10 = (float)*(int *)(param_1 + 0x104 + local_14 * 4) / local_8 + local_10;
    if (_DAT_100384b4 < local_10) break;
  }
  for (local_14 = 0; local_14 < 0x32 - local_c; local_14 = local_14 + 1) {
    *(undefined4 *)(param_1 + 0x38 + local_14 * 4) =
         *(undefined4 *)(param_1 + 0x38 + (local_c + local_14) * 4);
    *(undefined4 *)(param_1 + 0x104 + local_14 * 4) =
         *(undefined4 *)(param_1 + 0x104 + (local_c + local_14) * 4);
  }
  *(int *)(param_1 + 0x34) = *(int *)(param_1 + 0x34) - local_c;
  if (*(int *)(param_1 + 0x34) < 10) {
    *(undefined4 *)(param_1 + 0x34) = 10;
  }
  return;
}

//===== 0x1000ac91 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_1000ac91(int param_1)

{
  float fVar1;
  bool bVar2;
  bool bVar3;
  undefined3 extraout_var;
  int iVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  undefined3 extraout_var_00;
  int iVar8;
  undefined8 local_b4;
  int local_a4;
  int local_a0;
  int local_9c;
  undefined4 local_98;
  undefined4 uStack_94;
  double local_88;
  double local_78;
  int local_64;
  int local_5c;
  int local_58;
  float local_40;
  int local_34;
  int local_2c;
  int local_28;
  int local_1c;
  float local_18;
  int local_14;
  int local_10;
  int local_c;
  
  local_c = -1;
  local_34 = -1;
  local_58 = -1;
  local_28 = -1;
  local_5c = 0;
  local_18 = (float)*(int *)(param_1 + 0x38);
  local_40 = (float)*(int *)(param_1 + 0x34 + *(int *)(param_1 + 0x34) * 4) * _DAT_100384b8;
  if ((float)*(double *)(param_1 + 0x370) <= local_40) {
    local_40 = (float)((float10)_DAT_100384c0 * (float10)*(double *)(param_1 + 0x370));
  }
  if (local_18 < local_40 / _DAT_100384c8) {
    local_64 = 1;
    while ((local_64 <=
            (int)(*(int *)(param_1 + 0x34) + (*(int *)(param_1 + 0x34) >> 0x1f & 7U)) >> 3 &&
           (*(int *)(param_1 + 0x104 + local_5c * 4) < *(int *)(param_1 + 0x104 + local_64 * 4)))) {
      local_18 = (float)*(int *)(param_1 + 0x38 + local_64 * 4);
      local_5c = local_64;
      local_64 = local_64 + 1;
    }
  }
  iVar4 = *(int *)(param_1 + 0xc);
  if (*(int *)(param_1 + 0xc) < *(int *)(param_1 + 0x1c)) {
    bVar3 = false;
    bVar2 = FUN_1000b6db(*(int *)(param_1 + 0x20),*(int *)(param_1 + 0x1c),*(int *)(param_1 + 0xc),
                         *(int *)(param_1 + 0x368),
                         *(int *)(param_1 + 0x34 + *(int *)(param_1 + 0x34) * 4));
    if (CONCAT31(extraout_var,bVar2) != 0) {
      if (*(int *)(param_1 + 0x1c) - *(int *)(param_1 + 0xc) < 0xc9) {
        bVar3 = true;
      }
      else {
        local_88 = 0.0;
        local_78 = 0.0;
        for (local_14 = *(int *)(param_1 + 0xc); local_14 < *(int *)(param_1 + 0x1c) + -0x1e;
            local_14 = local_14 + 1) {
          if (((double)*(int *)(param_1 + 0x38) <=
               *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8)) &&
             (*(double *)(*(int *)(param_1 + 0x20) + local_14 * 8) <=
              (double)*(int *)(param_1 + 0x34 + *(int *)(param_1 + 0x34) * 4))) {
            local_88 = local_88 + *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8);
          }
        }
        for (local_14 = *(int *)(param_1 + 0x1c) + 0x1e; local_14 < *(int *)(param_1 + 0x368);
            local_14 = local_14 + 1) {
          if (((double)*(int *)(param_1 + 0x38) <=
               *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8)) &&
             (*(double *)(*(int *)(param_1 + 0x20) + local_14 * 8) <=
              (double)*(int *)(param_1 + 0x34 + *(int *)(param_1 + 0x34) * 4))) {
            local_78 = local_78 + *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8);
          }
        }
        if (local_88 < local_78) {
          bVar3 = true;
        }
      }
      if (bVar3) {
        local_98 = *(undefined4 *)(*(int *)(param_1 + 0x20) + *(int *)(param_1 + 0x1c) * 8);
        uStack_94 = *(undefined4 *)(*(int *)(param_1 + 0x20) + 4 + *(int *)(param_1 + 0x1c) * 8);
        local_10 = *(int *)(param_1 + 0x1c) + 1;
        for (local_14 = local_10; local_14 < *(int *)(param_1 + 0x1c) + 0x96;
            local_14 = local_14 + 1) {
          if ((*(double *)(*(int *)(param_1 + 0x20) + local_14 * 8) <
               (double)CONCAT44(uStack_94,local_98)) &&
             (_DAT_10038498 < *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8))) {
            local_98 = *(undefined4 *)(*(int *)(param_1 + 0x20) + local_14 * 8);
            uStack_94 = *(undefined4 *)(*(int *)(param_1 + 0x20) + 4 + local_14 * 8);
          }
        }
        if (local_18 < (float)(double)CONCAT44(uStack_94,local_98)) {
          local_b4 = (double)CONCAT44(uStack_94,local_98);
        }
        else {
          local_b4 = (double)local_18;
        }
        for (; iVar4 = local_10, local_10 < *(int *)(param_1 + 0x1c) + 0x96; local_10 = local_10 + 1
            ) {
          if ((*(double *)(*(int *)(param_1 + 0x20) + local_10 * 8) <= local_b4) &&
             (iVar5 = local_10,
             _DAT_10038498 != *(double *)(*(int *)(param_1 + 0x20) + local_10 * 8)))
          goto LAB_1000b155;
        }
      }
    }
  }
  goto LAB_1000b1a3;
  while (iVar4 = iVar5, iVar5 = local_10,
        *(double *)(*(int *)(param_1 + 0x20) + local_10 * 8) <=
        *(double *)(*(int *)(param_1 + 0x20) + -8 + local_10 * 8)) {
LAB_1000b155:
    local_10 = iVar5 + 1;
    iVar4 = local_10;
    if (*(int *)(param_1 + 0x1c) + 0x96 <= local_10) break;
  }
LAB_1000b1a3:
  local_10 = iVar4;
  iVar4 = ((*(int *)(param_1 + 0x368) - local_10) + 0x19) / 0x33;
  local_14 = local_10;
  for (local_2c = 0; local_2c < iVar4; local_2c = local_2c + 1) {
    local_a4 = 0;
    local_9c = 0;
    local_a0 = 0;
    local_1c = local_14 + 0x33;
    if (*(int *)(param_1 + 0x368) <= local_1c) {
      local_1c = *(int *)(param_1 + 0x368);
    }
    iVar8 = (local_1c - local_14) + 1;
    iVar5 = ftol();
    iVar5 = *(int *)(param_1 + 0x38 + iVar5 * 4);
    iVar6 = ftol();
    iVar6 = *(int *)(param_1 + 0x38 + iVar6 * 4);
    do {
      fVar1 = (float)*(double *)(*(int *)(param_1 + 0x20) + local_14 * 8);
      if ((((float)iVar5 <= fVar1) &&
          (local_a4 = local_a4 + 1, _DAT_100384b8 * (float)iVar6 <= fVar1)) &&
         (local_9c = local_9c + 1, local_a0 == 0)) {
        iVar7 = ftol();
        bVar3 = FUN_1000b6db(*(int *)(param_1 + 0x20),local_14,*(int *)(param_1 + 0xc),
                             *(int *)(param_1 + 0x368),iVar7);
        local_a0 = CONCAT31(extraout_var_00,bVar3);
      }
      local_14 = local_14 + 1;
    } while (local_14 < local_1c);
    if (iVar8 / 2 <= local_a4) {
      if (local_c == -1) {
        local_c = local_2c;
      }
      local_34 = local_2c;
    }
    if ((local_a0 != 0) || ((int)(iVar8 + (iVar8 >> 0x1f & 3U)) >> 2 <= local_9c)) {
      if (local_58 == -1) {
        local_58 = local_2c;
      }
      if ((local_28 == -1) && (iVar4 - local_2c < local_2c)) {
        local_28 = local_2c;
      }
    }
  }
  *(int *)(param_1 + 0x14) = local_10;
  *(undefined4 *)(param_1 + 0x18) = *(undefined4 *)(param_1 + 0x368);
  if (local_c != -1) {
    *(int *)(param_1 + 0x14) = local_10 + local_c * 0x33;
    *(int *)(param_1 + 0x18) = local_10 + (local_34 + 1) * 0x33;
    if (local_58 != -1) {
      if (local_58 <= local_c + 3) {
        *(int *)(param_1 + 0x14) = local_10 + (local_58 + 1) * 0x33;
      }
      if (iVar4 - local_28 < local_28) {
        *(int *)(param_1 + 0x18) = local_10 + (local_28 + -1) * 0x33;
      }
    }
    if (*(int *)(param_1 + 0x14) < 1) {
      *(undefined4 *)(param_1 + 0x14) = 1;
    }
    else if (*(int *)(param_1 + 0x368) < *(int *)(param_1 + 0x14)) {
      *(undefined4 *)(param_1 + 0x14) = *(undefined4 *)(param_1 + 0x368);
    }
    if (*(int *)(param_1 + 0x18) < 1) {
      *(undefined4 *)(param_1 + 0x18) = 1;
    }
    else if (*(int *)(param_1 + 0x368) < *(int *)(param_1 + 0x18)) {
      *(undefined4 *)(param_1 + 0x18) = *(undefined4 *)(param_1 + 0x368);
    }
    if (*(int *)(param_1 + 0x18) <= *(int *)(param_1 + 0x14)) {
      *(undefined4 *)(param_1 + 0x14) = 1;
      *(undefined4 *)(param_1 + 0x18) = 2;
    }
  }
  if (*(double *)(*(int *)(param_1 + 0x20) + *(int *)(param_1 + 0x14) * 8) <=
      (double)*(int *)(param_1 + 0x34 + *(int *)(param_1 + 0x34) * 4)) {
    for (local_14 = *(int *)(param_1 + 0x14); local_14 < *(int *)(param_1 + 0x14) + 0x33;
        local_14 = local_14 + 1) {
      if ((double)*(int *)(param_1 + 0x38 + local_5c * 4) <=
          *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8)) {
        local_14 = local_14 + -1;
        break;
      }
    }
  }
  else {
    for (local_14 = *(int *)(param_1 + 0x14);
        (local_14 < *(int *)(param_1 + 0x14) + 0x33 &&
        ((((double)*(int *)(param_1 + 0x34 + *(int *)(param_1 + 0x34) * 4) <=
           *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8) ||
          (*(double *)(*(int *)(param_1 + 0x20) + -8 + local_14 * 8) <=
           *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8))) ||
         (*(double *)(*(int *)(param_1 + 0x20) + 8 + local_14 * 8) <=
          *(double *)(*(int *)(param_1 + 0x20) + local_14 * 8))))); local_14 = local_14 + 1) {
    }
  }
  *(int *)(param_1 + 0x14) = local_14;
  return;
}

//===== 0x1000b6db =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

bool __cdecl FUN_1000b6db(int param_1,int param_2,int param_3,int param_4,int param_5)

{
  bool bVar1;
  int local_10;
  int local_c;
  
  bVar1 = false;
  if (_DAT_100384d0 < *(double *)(param_1 + param_2 * 8) / (double)param_5) {
    local_c = 0;
    for (local_10 = param_2;
        (param_3 <= local_10 && ((double)param_5 < *(double *)(param_1 + local_10 * 8)));
        local_10 = local_10 + -1) {
      local_c = local_c + 1;
    }
    while ((local_10 = param_2 + 1, local_10 < param_4 &&
           ((double)param_5 < *(double *)(param_1 + local_10 * 8)))) {
      local_c = local_c + 1;
      param_2 = local_10;
    }
    bVar1 = 9 < local_c;
  }
  return bVar1;
}

//===== 0x1000b7a0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __thiscall FUN_1000b7a0(void *this,Wvfm *param_1,int param_2,uint *param_3)

{
  int iVar1;
  double dVar2;
  double dVar3;
  double dVar4;
  undefined8 local_30;
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  
  if (param_2 != *(int *)(*(int *)((int)this + 0xa81c) + 0x1c060)) {
    *(int *)(*(int *)((int)this + 0xa81c) + 0x1c060) = param_2;
    if ((*param_3 >> 7 & 1) == 1) {
      param_2 = (param_2 * 0x11 + 5) / 10;
    }
    dVar4 = ((double)(param_2 * 2 + -2) * _DAT_10041bc8) / _DAT_100384d8;
    dVar4 = _DAT_100384e0 * dVar4 * dVar4;
    dVar2 = sqrt(_DAT_10041bc8 / dVar4);
    for (local_c = 1; local_c < 0x801; local_c = local_c + 1) {
      dVar3 = exp(-*(double *)(*(int *)((int)this + 0xa81c) + 0x18058 + local_c * 8) /
                  (_DAT_100384e8 * dVar4));
      *(double *)(*(int *)((int)this + 0xa81c) + 0x10048 + local_c * 8) = dVar3 * dVar2;
    }
  }
  if ((*param_3 >> 7 & 1) == 1) {
    local_8 = 1;
    for (local_c = 1; local_c < 0x801; local_c = local_c + 1) {
      dVar4 = Wvfm::sc_la(param_1,local_c,local_10);
      *(double *)(*(int *)((int)this + 0xa81c) + 0x38 + local_8 * 8) = dVar4;
      iVar1 = *(int *)((int)this + 0xa81c);
      *(undefined4 *)(iVar1 + 0x40 + local_8 * 8) = 0;
      *(undefined4 *)(iVar1 + 0x44 + local_8 * 8) = 0;
      local_8 = local_8 + 2;
    }
    dfour1((double *)(*(int *)((int)this + 0xa81c) + 0x38),0x800,1);
    FUN_1000bf17(*(int *)((int)this + 0xa81c) + 0x38,*(int *)((int)this + 0xa81c) + 0x10048,0x800);
    dfour1((double *)(*(int *)((int)this + 0xa81c) + 0x38),0x800,-1);
    FUN_1000bf65(*(int *)((int)this + 0xa81c) + 0x38,SUB84(_DAT_100384f0 / _DAT_100384d8,0),
                 (int)((ulonglong)(_DAT_100384f0 / _DAT_100384d8) >> 0x20),0x800);
    local_8 = 1;
    for (local_c = 1; local_c < 0x801; local_c = local_c + 1) {
      Wvfm::sc_la_set(param_1,local_c,local_10,
                      (double)CONCAT44(*(undefined4 *)
                                        (*(int *)((int)this + 0xa81c) + 0x3c + local_8 * 8),
                                       *(undefined4 *)
                                        (*(int *)((int)this + 0xa81c) + 0x38 + local_8 * 8)));
      local_8 = local_8 + 2;
    }
  }
  else {
    for (local_10 = 1; local_10 < 5; local_10 = local_10 + 1) {
      local_8 = 1;
      for (local_c = 1; local_c < 0x801; local_c = local_c + 1) {
        dVar4 = Wvfm::sc_la(param_1,local_c,local_10);
        *(double *)(*(int *)((int)this + 0xa81c) + 0x38 + local_8 * 8) = dVar4;
        iVar1 = *(int *)((int)this + 0xa81c);
        *(undefined4 *)(iVar1 + 0x40 + local_8 * 8) = 0;
        *(undefined4 *)(iVar1 + 0x44 + local_8 * 8) = 0;
        if (0x7c4 < local_c) {
          if (local_c < 0x7d4) {
            iVar1 = *(int *)((int)this + 0xa81c);
            dVar4 = cos((_DAT_100384f8 * _DAT_10041bc8 * (double)(local_c + -0x7c5)) / _DAT_10038500
                       );
            *(double *)(*(int *)((int)this + 0xa81c) + 0x38 + local_8 * 8) =
                 ((dVar4 + _DAT_100384f0) / _DAT_100384f8) * *(double *)(iVar1 + 0x38 + local_8 * 8)
            ;
          }
          else {
            iVar1 = *(int *)((int)this + 0xa81c);
            *(undefined4 *)(iVar1 + 0x38 + local_8 * 8) = 0;
            *(undefined4 *)(iVar1 + 0x3c + local_8 * 8) = 0;
          }
        }
        local_8 = local_8 + 2;
      }
      dfour1((double *)(*(int *)((int)this + 0xa81c) + 0x38),0x800,1);
      FUN_1000c027(*(int *)((int)this + 0xa81c) + 0x38,0x800);
      FUN_1000be99(*(int *)((int)this + 0xa81c) + 0x38,0x800);
      FUN_1000bfac(*(int *)((int)this + 0xa81c) + 0x38,*(int *)((int)this + 0xa81c) + 0x8040,1,0x800
                  );
      FUN_1000bfac(*(int *)((int)this + 0xa81c) + 0x38,*(int *)((int)this + 0xa81c) + 0x38,0,0x800);
      dfour1((double *)(*(int *)((int)this + 0xa81c) + 0x38),0x800,-1);
      FUN_1000bf65(*(int *)((int)this + 0xa81c) + 0x38,SUB84(_DAT_100384f0 / _DAT_100384d8,0),
                   (int)((ulonglong)(_DAT_100384f0 / _DAT_100384d8) >> 0x20),0x800);
      FUN_1000bf17(*(int *)((int)this + 0xa81c) + 0x38,*(int *)((int)this + 0xa81c) + 82000,0x800);
      dfour1((double *)(*(int *)((int)this + 0xa81c) + 0x38),0x800,1);
      FUN_1000bfac(*(int *)((int)this + 0xa81c) + 0x38,*(int *)((int)this + 0xa81c) + 0x38,0,0x800);
      FUN_1000be45(*(int *)((int)this + 0xa81c) + 0x38,*(int *)((int)this + 0xa81c) + 0x8040,0x800);
      FUN_1000bed8(*(int *)((int)this + 0xa81c) + 0x38,0x800);
      FUN_1000bf17(*(int *)((int)this + 0xa81c) + 0x38,*(int *)((int)this + 0xa81c) + 0x10048,0x800)
      ;
      dfour1((double *)(*(int *)((int)this + 0xa81c) + 0x38),0x800,-1);
      FUN_1000bf65(*(int *)((int)this + 0xa81c) + 0x38,SUB84(_DAT_100384f0 / _DAT_100384d8,0),
                   (int)((ulonglong)(_DAT_100384f0 / _DAT_100384d8) >> 0x20),0x800);
      local_30 = *(double *)(*(int *)((int)this + 0xa81c) + 0x40);
      local_8 = 1;
      for (local_c = 1; local_c < 0x801; local_c = local_c + 1) {
        if (local_30 < *(double *)(*(int *)((int)this + 0xa81c) + 0x38 + local_8 * 8)) {
          local_30 = (double)CONCAT44(*(undefined4 *)
                                       (*(int *)((int)this + 0xa81c) + 0x3c + local_8 * 8),
                                      *(undefined4 *)
                                       (*(int *)((int)this + 0xa81c) + 0x38 + local_8 * 8));
        }
        local_8 = local_8 + 2;
      }
      if (_DAT_100384e0 < local_30) {
        if (local_30 < _DAT_100384f0) {
          local_30 = local_30 * _DAT_100384f8;
        }
      }
      else {
        local_30 = 1.0;
      }
      local_8 = 1;
      for (local_c = 1; local_c < 0x801; local_c = local_c + 1) {
        Wvfm::sc_la_set(param_1,local_c,local_10,
                        *(double *)(*(int *)((int)this + 0xa81c) + 0x38 + local_8 * 8) / local_30);
        local_8 = local_8 + 2;
      }
    }
  }
  return;
}

//===== 0x1000be45 =====

void __cdecl FUN_1000be45(int param_1,int param_2,int param_3)

{
  undefined4 local_8;
  
  for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
    FUN_1003468c((void *)(param_1 + -8 + local_8 * 0x10),(double *)(param_2 + -8 + local_8 * 0x10));
  }
  return;
}

//===== 0x1000be99 =====

void __cdecl FUN_1000be99(int param_1,int param_2)

{
  undefined4 local_8;
  
  for (local_8 = 1; local_8 <= param_2; local_8 = local_8 + 1) {
    FUN_10034a20((double *)(param_1 + -8 + local_8 * 0x10));
  }
  return;
}

//===== 0x1000bed8 =====

void __cdecl FUN_1000bed8(int param_1,int param_2)

{
  undefined4 local_8;
  
  for (local_8 = 1; local_8 <= param_2; local_8 = local_8 + 1) {
    FUN_100349c7((double *)(param_1 + -8 + local_8 * 0x10));
  }
  return;
}

//===== 0x1000bf17 =====

void __cdecl FUN_1000bf17(int param_1,int param_2,int param_3)

{
  undefined4 local_8;
  
  for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
    FUN_10034a91((void *)(local_8 * 0x10 + param_1 + -8),
                 (double)CONCAT44(*(undefined4 *)(param_2 + 4 + local_8 * 8),
                                  *(undefined4 *)(param_2 + local_8 * 8)));
  }
  return;
}

//===== 0x1000bf65 =====

void __cdecl FUN_1000bf65(int param_1,undefined4 param_2,undefined4 param_3,int param_4)

{
  undefined4 local_8;
  
  for (local_8 = 1; local_8 <= param_4; local_8 = local_8 + 1) {
    FUN_10034a91((void *)(param_1 + -8 + local_8 * 0x10),(double)CONCAT44(param_3,param_2));
  }
  return;
}

//===== 0x1000bfac =====

void __cdecl FUN_1000bfac(int param_1,int param_2,int param_3,int param_4)

{
  undefined4 local_c;
  undefined4 local_8;
  
  if (param_3 == 0) {
    local_8 = 1;
    local_c = 1;
  }
  else {
    local_8 = 2;
    local_c = -1;
  }
  for (; local_8 <= param_4 * 2; local_8 = local_8 + 2) {
    *(undefined4 *)(param_2 + (local_8 + local_c) * 8) = 0;
    *(undefined4 *)(param_2 + 4 + (local_8 + local_c) * 8) = 0;
    *(undefined4 *)(param_2 + local_8 * 8) = *(undefined4 *)(param_1 + local_8 * 8);
    *(undefined4 *)(param_2 + 4 + local_8 * 8) = *(undefined4 *)(param_1 + 4 + local_8 * 8);
  }
  return;
}

//===== 0x1000c027 =====

void __cdecl FUN_1000c027(int param_1,int param_2)

{
  BandStat local_2c [16];
  int local_1c;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036ea9;
  local_10 = ExceptionList;
  local_18 = param_1 + -8;
  ExceptionList = &local_10;
  for (local_14 = 1; local_14 <= param_2; local_14 = local_14 + 1) {
    FUN_1000c100(local_2c,0,0,0,0);
    local_8 = 0;
    local_1c = FUN_1000c130((void *)(local_14 * 0x10 + local_18),(double *)local_2c);
    local_8 = 0xffffffff;
    BandStat::~BandStat(local_2c);
    if (local_1c != 0) {
      ATL::CFileTimeSpan::SetTimeSpan
                ((CFileTimeSpan *)(local_18 + local_14 * 0x10),0x3cb0000000000000);
    }
  }
  ExceptionList = local_10;
  return;
}

//===== 0x1000c0cf =====

void FUN_1000c0cf(void)

{
  FUN_1000c0d9();
  return;
}

//===== 0x1000c0d9 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1000c0d9(void)

{
  _DAT_10041bc8 = acos(-1.0);
  return;
}

//===== 0x1000c100 =====

undefined4 * __thiscall
FUN_1000c100(void *this,undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  *(undefined4 *)this = param_1;
  *(undefined4 *)((int)this + 4) = param_2;
  *(undefined4 *)((int)this + 8) = param_3;
  *(undefined4 *)((int)this + 0xc) = param_4;
  return this;
}

//===== 0x1000c130 =====

undefined4 __thiscall FUN_1000c130(void *this,double *param_1)

{
  undefined4 local_c;
  
  if ((*(double *)this == *param_1) && (*(double *)((int)this + 8) == param_1[1])) {
    local_c = 1;
  }
  else {
    local_c = 0;
  }
  return local_c;
}

//===== 0x1000c180 =====

/* Library Function - Single Match
    public: void __thiscall ATL::CFileTimeSpan::SetTimeSpan(__int64)
   
   Library: Visual Studio */

void __thiscall ATL::CFileTimeSpan::SetTimeSpan(CFileTimeSpan *this,__int64 param_1)

{
  *(__int64 *)this = param_1;
  return;
}

//===== 0x1000c1a0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Wvfm::CarlFullerMeasurement(void) */

void __thiscall Wvfm::CarlFullerMeasurement(Wvfm *this)

{
  float *pfVar1;
  long lVar2;
  float *pfVar3;
  float *pfVar4;
  int *piVar5;
  int iVar6;
  int iVar7;
  int local_78;
  float local_48;
  size_t local_40;
  int local_3c;
  int local_30;
  int local_24;
  int local_20;
  int local_18;
  int local_10;
  int local_c;
  int *local_8;
  
                    /* 0xc1a0  58  ?CarlFullerMeasurement@Wvfm@@AAEXXZ */
  lVar2 = *(long *)(this + 0xbc);
  local_20 = ((*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1) / 500;
  if (local_20 == 0) {
    local_20 = 1;
  }
  ObsInpSpec::setCFTblLen((ObsInpSpec *)(this + 0x210),local_20);
  pfVar3 = vector(1,lVar2);
  pfVar4 = vector(1,lVar2);
  local_8 = ivector(1,lVar2);
  piVar5 = ivector(1,lVar2);
  for (local_18 = 1; iVar6 = cols(this), local_18 <= iVar6; local_18 = local_18 + 1) {
    for (local_30 = *(int *)(this + 0xb8); local_30 <= *(int *)(this + 0xbc);
        local_30 = local_30 + 1) {
      pfVar3[local_30] =
           (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + local_30 * 4) + local_18 * 8);
    }
    FUN_1000c5fe((int)pfVar3,*(int *)(this + 0xb8),*(int *)(this + 0xbc),&local_10,&local_c,
                 (int)local_8,(int)piVar5);
    for (local_24 = 1; local_24 <= local_20; local_24 = local_24 + 1) {
      iVar6 = (local_24 + -1) * 500 + *(int *)(this + 0xb8);
      if (local_18 == 1) {
        ObsInpSpec::setCFTblBndry((ObsInpSpec *)(this + 0x210),local_24 + -1,iVar6,iVar6 + 499);
      }
      ObsInpSpec::setCFTblEntry((ObsInpSpec *)(this + 0x210),local_18 + -1,local_24 + -1,0,1);
      local_40 = 0;
      for (local_3c = local_10; local_3c <= local_c; local_3c = local_3c + 1) {
        iVar7 = local_8[local_3c];
        if (((iVar6 <= iVar7) && (iVar7 <= iVar6 + 499)) && (_DAT_10038510 < pfVar3[iVar7])) {
          local_40 = local_40 + 1;
          pfVar4[local_40] = pfVar3[iVar7];
        }
      }
      qsort(pfVar4 + 1,local_40,4,FUN_1000c5bc);
      for (local_3c = 1;
          pfVar4[local_3c] < (_DAT_10038514 * pfVar4[1] + pfVar4[local_40]) / _DAT_10038518;
          local_3c = local_3c + 1) {
      }
      if ((int)local_40 < 0x14) {
        local_78 = 1;
      }
      else {
        local_78 = (int)local_40 / 0x14;
      }
      iVar6 = (int)local_40 / 2;
      if (((local_78 != 0) && (iVar6 != 0)) && ((int)(local_3c + local_40 * 2) / 3 != 0)) {
        local_48 = 0.0;
        pfVar1 = pfVar4 + local_78;
        while (local_40 = local_78 + 1, (int)local_40 <= iVar6) {
          local_78 = local_40;
          if (_DAT_10038510 < pfVar4[local_40] - *pfVar1) {
            local_48 = local_48 + (float)(int)local_40 / (float)iVar6;
          }
        }
        if (_DAT_10038510 != local_48) {
          iVar6 = ftol();
          iVar7 = ftol();
          ObsInpSpec::setCFTblEntry
                    ((ObsInpSpec *)(this + 0x210),local_18 + -1,local_24 + -1,iVar7,iVar6);
        }
      }
    }
  }
  free_vector(pfVar3,1,lVar2);
  free_ivector(local_8,1,lVar2);
  free_ivector(piVar5,1,lVar2);
  free_vector(pfVar4,1,lVar2);
  return;
}

//===== 0x1000c5bc =====

undefined4 __cdecl FUN_1000c5bc(float *param_1,float *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x1000c5fe =====

void __cdecl
FUN_1000c5fe(int param_1,int param_2,int param_3,int *param_4,int *param_5,int param_6,int param_7)

{
  float fVar1;
  int iVar2;
  int local_14;
  int local_10;
  float local_c;
  int local_8;
  
  local_14 = 0;
  *param_5 = 0;
  local_8 = 0;
  fVar1 = *(float *)(param_1 + param_2 * 4);
  while (iVar2 = param_2, local_c = fVar1, local_10 = iVar2 + 1, local_10 <= param_3) {
    fVar1 = *(float *)(param_1 + local_10 * 4);
    if (local_14 == 0) {
      if (fVar1 <= local_c) {
        param_2 = local_10;
        if (fVar1 < local_c) {
          local_14 = 2;
          *param_5 = *param_5 + 1;
          *(int *)(param_6 + *param_5 * 4) = iVar2;
          local_8 = local_8 + 1;
          *(int *)(param_7 + local_8 * 4) = local_10;
          param_2 = local_10;
        }
      }
      else {
        local_14 = 1;
        local_8 = local_8 + 1;
        *(int *)(param_7 + local_8 * 4) = iVar2;
        *param_5 = *param_5 + 1;
        *(int *)(param_6 + *param_5 * 4) = local_10;
        param_2 = local_10;
      }
    }
    else if (local_14 == 1) {
      if (fVar1 <= local_c) {
        param_2 = local_10;
        if (fVar1 < local_c) {
          local_14 = 2;
          *(int *)(param_6 + *param_5 * 4) = iVar2;
          local_8 = local_8 + 1;
          *(int *)(param_7 + local_8 * 4) = local_10;
          param_2 = local_10;
        }
      }
      else {
        *(int *)(param_6 + *param_5 * 4) = local_10;
        param_2 = local_10;
      }
    }
    else {
      param_2 = local_10;
      if (local_14 == 2) {
        if (fVar1 <= local_c) {
          *(int *)(param_7 + local_8 * 4) = local_10;
          param_2 = local_10;
        }
        else {
          local_14 = 1;
          *(int *)(param_7 + local_8 * 4) = iVar2;
          *param_5 = *param_5 + 1;
          *(int *)(param_6 + *param_5 * 4) = local_10;
          param_2 = local_10;
        }
      }
    }
  }
  if ((*param_5 != 0) && (local_8 != 0)) {
    *param_4 = 1;
    if (*(int *)(param_6 + *param_4 * 4) < *(int *)(param_7 + 4)) {
      *param_4 = *param_4 + 1;
    }
    if (*(int *)(param_7 + local_8 * 4) < *(int *)(param_6 + *param_5 * 4)) {
      *param_5 = *param_5 + -1;
    }
    if (*param_5 < *param_4) {
      *param_5 = 0;
    }
  }
  return;
}

//===== 0x1000c83a =====

void FUN_1000c83a(void)

{
  FUN_1000c844();
  return;
}

//===== 0x1000c844 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1000c844(void)

{
  _DAT_10041c30 = acos(-1.0);
  return;
}

//===== 0x1000c860 =====

/* public: __thiscall CSIBQWrap::CSIBQWrap(int,enum CSIBQWrap::PHYSDATA) */

CSIBQWrap * __thiscall CSIBQWrap::CSIBQWrap(CSIBQWrap *this,int param_1,PHYSDATA param_2)

{
  undefined4 *puVar1;
  undefined4 *local_50;
  uint local_40;
  int local_3c [11];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0xc860  8  ??0CSIBQWrap@@QAE@HW4PHYSDATA@0@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036ecb;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  local_3c[0] = 0x11011345;
  local_3c[1] = 6;
  local_3c[2] = 0x1a56937;
  local_3c[3] = 2;
  local_3c[4] = 0x234ffe97;
  local_3c[5] = 4;
  local_3c[6] = 0x3579bdf0;
  local_3c[7] = 5;
  local_3c[8] = 0xae120400;
  local_3c[9] = 7;
  local_3c[10] = 0;
  local_40 = 0;
  do {
    if (4 < local_40) {
LAB_1000c908:
      puVar1 = operator_new(0x708);
      local_8 = 0;
      if (puVar1 == (undefined4 *)0x0) {
        local_50 = (undefined4 *)0x0;
      }
      else {
        local_50 = FUN_1000d4e0(puVar1);
      }
      local_8 = 0xffffffff;
      *(undefined4 **)this = local_50;
      if (*(int *)this == 0) {
        FUN_1000d4a0(*(void **)this,1);
      }
      else if (local_3c[10] == 0) {
        FUN_1000d4a0(*(void **)this,2);
      }
      else {
        RdrOut::iS1(*(RdrOut **)this,local_3c[local_40 * 2 + 1]);
        BandStat::bbgn(*(BandStat **)this,param_2);
      }
      ExceptionList = local_10;
      return this;
    }
    if (local_3c[local_40 * 2] == param_1) {
      local_3c[10] = 1;
      goto LAB_1000c908;
    }
    local_40 = local_40 + 1;
  } while( true );
}

//===== 0x1000c9ab =====

/* public: __thiscall CSIBQWrap::CSIBQWrap(class CSIBQWrap const &) */

CSIBQWrap * __thiscall CSIBQWrap::CSIBQWrap(CSIBQWrap *this,CSIBQWrap *param_1)

{
                    /* 0xc9ab  7  ??0CSIBQWrap@@QAE@ABV0@@Z */
  *(undefined4 *)this = 0;
  operator=(this,param_1);
  return this;
}

//===== 0x1000c9d0 =====

/* public: class CSIBQWrap const & __thiscall CSIBQWrap::operator=(class CSIBQWrap const &) */

CSIBQWrap * __thiscall CSIBQWrap::operator=(CSIBQWrap *this,CSIBQWrap *param_1)

{
                    /* 0xc9d0  46  ??4CSIBQWrap@@QAEABV0@ABV0@@Z */
  if (param_1 != this) {
    FUN_1000da57(*(void **)this,*(undefined4 **)param_1);
  }
  return this;
}

//===== 0x1000c9f8 =====

/* public: __thiscall CSIBQWrap::~CSIBQWrap(void) */

void __thiscall CSIBQWrap::~CSIBQWrap(CSIBQWrap *this)

{
                    /* 0xc9f8  33  ??1CSIBQWrap@@QAE@XZ */
  if (*(void **)this != (void *)0x0) {
    FUN_1000d220(*(void **)this,1);
  }
  *(undefined4 *)this = 0;
  return;
}

//===== 0x1000ca38 =====

/* public: int __thiscall CSIBQWrap::setTrace(struct CSIDataRow * const,int) */

int __thiscall CSIBQWrap::setTrace(CSIBQWrap *this,CSIDataRow *param_1,int param_2)

{
  bool bVar1;
  undefined3 extraout_var;
  
                    /* 0xca38  381  ?setTrace@CSIBQWrap@@QAEHQAUCSIDataRow@@H@Z */
  bVar1 = FUN_1000df0e(*(void **)this,(int)param_1,param_2);
  return CONCAT31(extraout_var,bVar1);
}

//===== 0x1000ca57 =====

/* public: int __thiscall CSIBQWrap::setCurrent(float const * const,int) */

int __thiscall CSIBQWrap::setCurrent(CSIBQWrap *this,float *param_1,int param_2)

{
  bool bVar1;
  undefined3 extraout_var;
  
                    /* 0xca57  365  ?setCurrent@CSIBQWrap@@QAEHQBMH@Z */
  bVar1 = FUN_1000e02e(*(void **)this,(int)param_1,param_2);
  return CONCAT31(extraout_var,bVar1);
}

//===== 0x1000ca76 =====

/* public: int __thiscall CSIBQWrap::setLaneOrder(char const *) */

int __thiscall CSIBQWrap::setLaneOrder(CSIBQWrap *this,char *param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  
                    /* 0xca76  367  ?setLaneOrder@CSIBQWrap@@QAEHPBD@Z */
  bVar1 = FUN_1000e37a(*(void **)this,param_1);
  return CONCAT31(extraout_var,bVar1);
}

//===== 0x1000ca91 =====

/* public: int __thiscall CSIBQWrap::setBgnEnd(int,int) */

int __thiscall CSIBQWrap::setBgnEnd(CSIBQWrap *this,int param_1,int param_2)

{
  bool bVar1;
  undefined3 extraout_var;
  
                    /* 0xca91  355  ?setBgnEnd@CSIBQWrap@@QAEHHH@Z */
  bVar1 = FUN_1000d400(*(void **)this,param_1,param_2);
  return CONCAT31(extraout_var,bVar1);
}

//===== 0x1000cab0 =====

/* public: int __thiscall CSIBQWrap::setSpecSepClue(struct CSIDataRow * const) */

int __thiscall CSIBQWrap::setSpecSepClue(CSIBQWrap *this,CSIDataRow *param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  
                    /* 0xcab0  376  ?setSpecSepClue@CSIBQWrap@@QAEHQAUCSIDataRow@@@Z */
  bVar1 = FUN_1000e3ea(*(void **)this,(int)param_1);
  return CONCAT31(extraout_var,bVar1);
}

//===== 0x1000cacb =====

/* public: int __thiscall CSIBQWrap::setSpecSepMtrx(struct CSIDataRow * const) */

int __thiscall CSIBQWrap::setSpecSepMtrx(CSIBQWrap *this,CSIDataRow *param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  
                    /* 0xcacb  378  ?setSpecSepMtrx@CSIBQWrap@@QAEHQAUCSIDataRow@@@Z */
  bVar1 = FUN_1000e46d(*(void **)this,(int)param_1);
  return CONCAT31(extraout_var,bVar1);
}

//===== 0x1000cae6 =====

/* public: int __thiscall CSIBQWrap::setBeautifyOptions(int,int,int,int,int) */

int __thiscall
CSIBQWrap::setBeautifyOptions
          (CSIBQWrap *this,int param_1,int param_2,int param_3,int param_4,int param_5)

{
  bool bVar1;
  undefined3 extraout_var;
  
                    /* 0xcae6  354  ?setBeautifyOptions@CSIBQWrap@@QAEHHHHHH@Z */
  bVar1 = FUN_1000d440(*(void **)this,param_1,param_2,param_3,param_4,param_5);
  return CONCAT31(extraout_var,bVar1);
}

//===== 0x1000cb11 =====

/* public: void __thiscall CSIBQWrap::setTestOptions(struct TestOptions) */

void __thiscall CSIBQWrap::setTestOptions(CSIBQWrap *this,undefined4 param_2)

{
                    /* 0xcb11  380  ?setTestOptions@CSIBQWrap@@QAEXUTestOptions@@@Z */
  FUN_1000d4c0(*(void **)this,param_2);
  return;
}

//===== 0x1000cb2c =====

/* public: void __thiscall CSIBQWrap::getTestOptions(struct TestOptions &)const  */

void __thiscall CSIBQWrap::getTestOptions(CSIBQWrap *this,TestOptions *param_1)

{
  undefined4 *puVar1;
  
                    /* 0xcb2c  222  ?getTestOptions@CSIBQWrap@@QBEXAAUTestOptions@@@Z */
  puVar1 = (undefined4 *)FUN_1000d370(*(int *)this);
  *(undefined4 *)param_1 = *puVar1;
  return;
}

//===== 0x1000cb4a =====

/* public: void __thiscall CSIBQWrap::annotate(int) */

void __thiscall CSIBQWrap::annotate(CSIBQWrap *this,int param_1)

{
                    /* 0xcb4a  68  ?annotate@CSIBQWrap@@QAEXH@Z */
  FUN_1000e3cb(*(void **)this,param_1);
  return;
}

//===== 0x1000cb65 =====

/* public: class Annotate const * __thiscall CSIBQWrap::getAnnotation(void)const  */

Annotate * __thiscall CSIBQWrap::getAnnotation(CSIBQWrap *this)

{
  RdrOut *this_00;
  Wvfm *this_01;
  Annotate *pAVar1;
  
                    /* 0xcb65  174  ?getAnnotation@CSIBQWrap@@QBEPBVAnnotate@@XZ */
  this_00 = (RdrOut *)FUN_1000d290(*(int *)this);
  this_01 = RdrOut::wvfm(this_00);
  pAVar1 = Wvfm::getAnnotation(this_01);
  return pAVar1;
}

//===== 0x1000cb88 =====

/* public: void __thiscall CSIBQWrap::getRBgnEndScnl(int &,int &)const  */

void __thiscall CSIBQWrap::getRBgnEndScnl(CSIBQWrap *this,int *param_1,int *param_2)

{
                    /* 0xcb88  207  ?getRBgnEndScnl@CSIBQWrap@@QBEXAAH0@Z */
  FUN_1000d390(*(void **)this,param_1,param_2);
  return;
}

//===== 0x1000cba7 =====

/* public: int __thiscall CSIBQWrap::doBaseCalling(void) */

int __thiscall CSIBQWrap::doBaseCalling(CSIBQWrap *this)

{
  int iVar1;
  
                    /* 0xcba7  143  ?doBaseCalling@CSIBQWrap@@QAEHXZ */
  iVar1 = FUN_1000e123(*(int **)this);
  return iVar1;
}

//===== 0x1000cbbc =====

/* public: int __thiscall CSIBQWrap::doSmplRateCnvrt(void) */

int __thiscall CSIBQWrap::doSmplRateCnvrt(CSIBQWrap *this)

{
  int iVar1;
  TestOptions *pTVar2;
  Wvfm *this_00;
  
                    /* 0xcbbc  144  ?doSmplRateCnvrt@CSIBQWrap@@QAEHXZ */
  iVar1 = FUN_1000f339(*(int **)this);
  if (iVar1 != 0) {
    pTVar2 = (TestOptions *)FUN_1000d370(*(int *)this);
    this_00 = (Wvfm *)FUN_1000d270(*(int *)this);
    Wvfm::rawRateCnvrt(this_00,pTVar2);
  }
  return iVar1;
}

//===== 0x1000cbfb =====

/* public: char const * __thiscall CSIBQWrap::laneOrder(void)const  */

char * __thiscall CSIBQWrap::laneOrder(CSIBQWrap *this)

{
  char *pcVar1;
  
                    /* 0xcbfb  254  ?laneOrder@CSIBQWrap@@QBEPBDXZ */
  pcVar1 = (char *)FUN_1000d2f0(*(int *)this);
  return pcVar1;
}

//===== 0x1000cc10 =====

/* public: int __thiscall CSIBQWrap::getSpecSepClue(struct CSIDataRow * const)const  */

int __thiscall CSIBQWrap::getSpecSepClue(CSIBQWrap *this,CSIDataRow *param_1)

{
  uint uVar1;
  int iVar2;
  CSIDataRow *pCVar3;
  undefined4 *puVar4;
  int local_c;
  int local_8;
  
                    /* 0xcc10  216  ?getSpecSepClue@CSIBQWrap@@QBEHQAUCSIDataRow@@@Z */
  local_8 = 0;
  uVar1 = FUN_1000d2b0(*(void **)this,0x40);
  if (uVar1 != 0) {
    iVar2 = FUN_1000d330(*(int *)this);
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      puVar4 = (undefined4 *)(iVar2 + local_c * 0x10);
      pCVar3 = param_1 + local_c * 0x10;
      *(undefined4 *)pCVar3 = *puVar4;
      *(undefined4 *)(pCVar3 + 4) = puVar4[1];
      *(undefined4 *)(pCVar3 + 8) = puVar4[2];
      *(undefined4 *)(pCVar3 + 0xc) = puVar4[3];
    }
    local_8 = 1;
  }
  return local_8;
}

//===== 0x1000cc93 =====

/* public: int __thiscall CSIBQWrap::getSpecSepMtrx(struct CSIDataRow * const)const  */

int __thiscall CSIBQWrap::getSpecSepMtrx(CSIBQWrap *this,CSIDataRow *param_1)

{
  uint uVar1;
  int iVar2;
  CSIDataRow *pCVar3;
  undefined4 *puVar4;
  int local_c;
  int local_8;
  
                    /* 0xcc93  218  ?getSpecSepMtrx@CSIBQWrap@@QBEHQAUCSIDataRow@@@Z */
  local_8 = 0;
  uVar1 = FUN_1000d2b0(*(void **)this,0x40);
  if (uVar1 != 0) {
    iVar2 = FUN_1000d350(*(int *)this);
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      puVar4 = (undefined4 *)(iVar2 + local_c * 0x10);
      pCVar3 = param_1 + local_c * 0x10;
      *(undefined4 *)pCVar3 = *puVar4;
      *(undefined4 *)(pCVar3 + 4) = puVar4[1];
      *(undefined4 *)(pCVar3 + 8) = puVar4[2];
      *(undefined4 *)(pCVar3 + 0xc) = puVar4[3];
    }
    local_8 = 1;
  }
  return local_8;
}

//===== 0x1000cd16 =====

/* public: int __thiscall CSIBQWrap::getSRCLength(void)const  */

int __thiscall CSIBQWrap::getSRCLength(CSIBQWrap *this)

{
  Wvfm *pWVar1;
  int iVar2;
  
                    /* 0xcd16  213  ?getSRCLength@CSIBQWrap@@QBEHXZ */
  pWVar1 = (Wvfm *)FUN_1000d270(*(int *)this);
  iVar2 = FUN_1000d2d0(pWVar1);
  return iVar2;
}

//===== 0x1000cd36 =====

/* public: int __thiscall CSIBQWrap::getOutLength(void)const  */

int __thiscall CSIBQWrap::getOutLength(CSIBQWrap *this)

{
  RdrOut *this_00;
  Wvfm *pWVar1;
  int iVar2;
  
                    /* 0xcd36  200  ?getOutLength@CSIBQWrap@@QBEHXZ */
  this_00 = (RdrOut *)FUN_1000d290(*(int *)this);
  pWVar1 = RdrOut::wvfm(this_00);
  iVar2 = FUN_1000d2d0(pWVar1);
  return iVar2;
}

//===== 0x1000cd65 =====

/* public: int __thiscall CSIBQWrap::getSRCTrace(struct CSIDataRow * const)const  */

int __thiscall CSIBQWrap::getSRCTrace(CSIBQWrap *this,CSIDataRow *param_1)

{
  int iVar1;
  Wvfm *pWVar2;
  
                    /* 0xcd65  214  ?getSRCTrace@CSIBQWrap@@QBEHQAUCSIDataRow@@@Z */
  iVar1 = getSRCLength(this);
  pWVar2 = (Wvfm *)FUN_1000d270(*(int *)this);
  iVar1 = FUN_1000ef40(pWVar2,(int)param_1,iVar1);
  return iVar1;
}

//===== 0x1000cd94 =====

/* public: int __thiscall CSIBQWrap::getSRCCurrent(float * const)const  */

int __thiscall CSIBQWrap::getSRCCurrent(CSIBQWrap *this,float *param_1)

{
  int iVar1;
  Wvfm *pWVar2;
  
                    /* 0xcd94  211  ?getSRCCurrent@CSIBQWrap@@QBEHQAM@Z */
  iVar1 = getSRCLength(this);
  pWVar2 = (Wvfm *)FUN_1000d270(*(int *)this);
  iVar1 = FUN_1000efd3(pWVar2,(int)param_1,iVar1);
  return iVar1;
}

//===== 0x1000cdc3 =====

/* public: int __thiscall CSIBQWrap::getOutTrace(struct CSIDataRow * const)const  */

int __thiscall CSIBQWrap::getOutTrace(CSIBQWrap *this,CSIDataRow *param_1)

{
  int iVar1;
  RdrOut *this_00;
  Wvfm *pWVar2;
  
                    /* 0xcdc3  201  ?getOutTrace@CSIBQWrap@@QBEHQAUCSIDataRow@@@Z */
  iVar1 = getOutLength(this);
  this_00 = (RdrOut *)FUN_1000d290(*(int *)this);
  pWVar2 = RdrOut::wvfm(this_00);
  iVar1 = FUN_1000ef40(pWVar2,(int)param_1,iVar1);
  return iVar1;
}

//===== 0x1000cdf9 =====

/* public: int __thiscall CSIBQWrap::getOutCurrent(float * const)const  */

int __thiscall CSIBQWrap::getOutCurrent(CSIBQWrap *this,float *param_1)

{
  int iVar1;
  RdrOut *this_00;
  Wvfm *pWVar2;
  
                    /* 0xcdf9  199  ?getOutCurrent@CSIBQWrap@@QBEHQAM@Z */
  iVar1 = getOutLength(this);
  this_00 = (RdrOut *)FUN_1000d290(*(int *)this);
  pWVar2 = RdrOut::wvfm(this_00);
  iVar1 = FUN_1000efd3(pWVar2,(int)param_1,iVar1);
  return iVar1;
}

//===== 0x1000ce2f =====

/* public: int __thiscall CSIBQWrap::getInputAlignment(void)const  */

int __thiscall CSIBQWrap::getInputAlignment(CSIBQWrap *this)

{
  Wvfm *this_00;
  int iVar1;
  
                    /* 0xce2f  189  ?getInputAlignment@CSIBQWrap@@QBEHXZ */
  this_00 = (Wvfm *)FUN_1000d250(*(int *)this);
  iVar1 = Wvfm::obgni(this_00);
  return iVar1;
}

//===== 0x1000ce4b =====

/* public: int __thiscall CSIBQWrap::getSRCBgnScnl(void)const  */

int __thiscall CSIBQWrap::getSRCBgnScnl(CSIBQWrap *this)

{
  Wvfm *this_00;
  int iVar1;
  
                    /* 0xce4b  210  ?getSRCBgnScnl@CSIBQWrap@@QBEHXZ */
  this_00 = (Wvfm *)FUN_1000d270(*(int *)this);
  iVar1 = Wvfm::obgni(this_00);
  return iVar1;
}

//===== 0x1000ce67 =====

void FUN_1000ce67(void)

{
  FUN_1000ce71();
  return;
}

//===== 0x1000ce71 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1000ce71(void)

{
  _DAT_10041c98 = acos(-1.0);
  return;
}

//===== 0x1000ce8b =====

/* public: int __thiscall CSIBQWrap::getSRCEndScnl(void)const  */

int __thiscall CSIBQWrap::getSRCEndScnl(CSIBQWrap *this)

{
  Wvfm *this_00;
  int iVar1;
  
                    /* 0xce8b  212  ?getSRCEndScnl@CSIBQWrap@@QBEHXZ */
  this_00 = (Wvfm *)FUN_1000d270(*(int *)this);
  iVar1 = Wvfm::oendi(this_00);
  return iVar1;
}

//===== 0x1000cea7 =====

/* public: int __thiscall CSIBQWrap::getBgnScnl(void)const  */

int __thiscall CSIBQWrap::getBgnScnl(CSIBQWrap *this)

{
  Wvfm *this_00;
  int iVar1;
  
                    /* 0xcea7  176  ?getBgnScnl@CSIBQWrap@@QBEHXZ */
  this_00 = (Wvfm *)FUN_1000d250(*(int *)this);
  iVar1 = Wvfm::obgni(this_00);
  return iVar1;
}

//===== 0x1000cec3 =====

/* public: int __thiscall CSIBQWrap::getEndScnl(void)const  */

int __thiscall CSIBQWrap::getEndScnl(CSIBQWrap *this)

{
  Wvfm *this_00;
  int iVar1;
  
                    /* 0xcec3  185  ?getEndScnl@CSIBQWrap@@QBEHXZ */
  this_00 = (Wvfm *)FUN_1000d250(*(int *)this);
  iVar1 = Wvfm::oendi(this_00);
  return iVar1;
}

//===== 0x1000cee7 =====

/* public: int __thiscall CSIBQWrap::getNumBases(void)const  */

int __thiscall CSIBQWrap::getNumBases(CSIBQWrap *this)

{
  int iVar1;
  
                    /* 0xcee7  196  ?getNumBases@CSIBQWrap@@QBEHXZ */
  iVar1 = FUN_1000d310(*(int *)this);
  return iVar1;
}

//===== 0x1000cefc =====

/* public: char const * __thiscall CSIBQWrap::getSequence(void) */

char * __thiscall CSIBQWrap::getSequence(CSIBQWrap *this)

{
  char *pcVar1;
  
                    /* 0xcefc  215  ?getSequence@CSIBQWrap@@QAEPBDXZ */
  pcVar1 = (char *)FUN_1000f03a(*(int **)this);
  return pcVar1;
}

//===== 0x1000cf11 =====

/* public: char const * __thiscall CSIBQWrap::getIUBCodes(void) */

char * __thiscall CSIBQWrap::getIUBCodes(CSIBQWrap *this)

{
  char *pcVar1;
  
                    /* 0xcf11  187  ?getIUBCodes@CSIBQWrap@@QAEPBDXZ */
  pcVar1 = (char *)FUN_1000f06f(*(int **)this);
  return pcVar1;
}

//===== 0x1000cf26 =====

/* public: struct CSIDataRow const * __thiscall CSIBQWrap::getIUBValues(void) */

CSIDataRow * __thiscall CSIBQWrap::getIUBValues(CSIBQWrap *this)

{
  CSIDataRow *pCVar1;
  
                    /* 0xcf26  188  ?getIUBValues@CSIBQWrap@@QAEPBUCSIDataRow@@XZ */
  pCVar1 = (CSIDataRow *)FUN_1000f0a4(*(int **)this);
  return pCVar1;
}

//===== 0x1000cf3b =====

/* public: float const * __thiscall CSIBQWrap::getQualVec(void) */

float * __thiscall CSIBQWrap::getQualVec(CSIBQWrap *this)

{
  float *pfVar1;
  
                    /* 0xcf3b  206  ?getQualVec@CSIBQWrap@@QAEPBMXZ */
  pfVar1 = (float *)FUN_1000f10e(*(int **)this);
  return pfVar1;
}

//===== 0x1000cf50 =====

/* public: int const * __thiscall CSIBQWrap::getPeakPosn(void) */

int * __thiscall CSIBQWrap::getPeakPosn(CSIBQWrap *this)

{
  int *piVar1;
  
                    /* 0xcf50  202  ?getPeakPosn@CSIBQWrap@@QAEPBHXZ */
  piVar1 = (int *)FUN_1000f0d9(*(int **)this);
  return piVar1;
}

//===== 0x1000cf65 =====

/* public: int __thiscall CSIBQWrap::getLeftClip(void)const  */

int __thiscall CSIBQWrap::getLeftClip(CSIBQWrap *this)

{
  RdrOut *this_00;
  QualCtrl *this_01;
  SSNODE *this_02;
  int iVar1;
  
                    /* 0xcf65  190  ?getLeftClip@CSIBQWrap@@QBEHXZ */
  this_00 = (RdrOut *)FUN_1000d290(*(int *)this);
  this_01 = RdrOut::qualctrl(this_00);
  this_02 = QualCtrl::cutdata(this_01);
  iVar1 = Annotate::getNumCurrFix((Annotate *)this_02);
  return iVar1;
}

//===== 0x1000cf8f =====

/* public: int __thiscall CSIBQWrap::getRightClip(void)const  */

int __thiscall CSIBQWrap::getRightClip(CSIBQWrap *this)

{
  RdrOut *pRVar1;
  QualCtrl *pQVar2;
  SSNODE *pSVar3;
  int iVar4;
  
                    /* 0xcf8f  209  ?getRightClip@CSIBQWrap@@QBEHXZ */
  pRVar1 = (RdrOut *)FUN_1000d290(*(int *)this);
  pQVar2 = RdrOut::qualctrl(pRVar1);
  pSVar3 = QualCtrl::cutdata(pQVar2);
  SW::alignedLength((SW *)pSVar3);
  pRVar1 = (RdrOut *)FUN_1000d290(*(int *)this);
  RdrOut::getXOverCut(pRVar1);
  pRVar1 = (RdrOut *)FUN_1000d290(*(int *)this);
  pQVar2 = RdrOut::qualctrl(pRVar1);
  pSVar3 = QualCtrl::cutdata(pQVar2);
  iVar4 = SW::alignedLength((SW *)pSVar3);
  return iVar4;
}

//===== 0x1000d005 =====

/* public: char const * __thiscall CSIBQWrap::sfwrName(void)const  */

char * __thiscall CSIBQWrap::sfwrName(CSIBQWrap *this)

{
  char *pcVar1;
  AboutBQ local_14 [4];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0xd005  383  ?sfwrName@CSIBQWrap@@QBEPBDXZ */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036ede;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  AboutBQ::AboutBQ(local_14);
  local_8 = 0;
  pcVar1 = AboutBQ::productName(local_14);
  local_8 = 0xffffffff;
  AboutBQ::~AboutBQ(local_14);
  ExceptionList = local_10;
  return pcVar1;
}

//===== 0x1000d05d =====

/* public: float __thiscall CSIBQWrap::sfwrVersion(void)const  */

float __thiscall CSIBQWrap::sfwrVersion(CSIBQWrap *this)

{
  float fVar1;
  AboutBQ local_14 [4];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0xd05d  385  ?sfwrVersion@CSIBQWrap@@QBEMXZ */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036ef1;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  AboutBQ::AboutBQ(local_14);
  local_8 = 0;
  fVar1 = AboutBQ::productVersion(local_14);
  local_8 = 0xffffffff;
  AboutBQ::~AboutBQ(local_14);
  ExceptionList = local_10;
  return fVar1;
}

//===== 0x1000d0b5 =====

/* public: char const * __thiscall CSIBQWrap::sfwrPatents(void)const  */

char * __thiscall CSIBQWrap::sfwrPatents(CSIBQWrap *this)

{
  char *pcVar1;
  AboutBQ local_14 [4];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0xd0b5  384  ?sfwrPatents@CSIBQWrap@@QBEPBDXZ */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036f04;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  AboutBQ::AboutBQ(local_14);
  local_8 = 0;
  pcVar1 = AboutBQ::productPatents(local_14);
  local_8 = 0xffffffff;
  AboutBQ::~AboutBQ(local_14);
  ExceptionList = local_10;
  return pcVar1;
}

//===== 0x1000d10d =====

/* public: int __thiscall CSIBQWrap::getStatus(void)const  */

int __thiscall CSIBQWrap::getStatus(CSIBQWrap *this)

{
  int iVar1;
  
                    /* 0xd10d  220  ?getStatus@CSIBQWrap@@QBEHXZ */
  iVar1 = FUN_1000f508(*(undefined4 **)this);
  return iVar1;
}

//===== 0x1000d122 =====

/* public: char const * __thiscall CSIBQWrap::getStatusMsg(void)const  */

char * __thiscall CSIBQWrap::getStatusMsg(CSIBQWrap *this)

{
  char *pcVar1;
  
                    /* 0xd122  221  ?getStatusMsg@CSIBQWrap@@QBEPBDXZ */
  pcVar1 = FUN_1000f690(*(uint **)this);
  return pcVar1;
}

//===== 0x1000d137 =====

/* public: int __thiscall CSIBQWrap::licensed(void) */

int __thiscall CSIBQWrap::licensed(CSIBQWrap *this)

{
  int iVar1;
  
                    /* 0xd137  263  ?licensed@CSIBQWrap@@QAEHXZ */
  iVar1 = FUN_1000ded1();
  return iVar1;
}

//===== 0x1000d14c =====

/* public: void __thiscall CSIBQWrap::postMortem(void)const  */

void __thiscall CSIBQWrap::postMortem(CSIBQWrap *this)

{
  int iVar1;
  int iVar2;
  int local_18;
  char *local_14;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0xd14c  307  ?postMortem@CSIBQWrap@@QBEXXZ */
  iVar1 = getStatus(this);
  if (iVar1 != 1) {
    getMajorMinor(this,&local_8,&local_c,&local_14);
    getRBgnEndScnl(this,&local_10,&local_18);
    fprintf((FILE *)(_iob_exref + 0x40),s_Failure__Major__d_Minor__d_Messg_1003f384,local_8,local_c,
            local_14);
    iVar1 = getEndScnl(this);
    iVar2 = getBgnScnl(this);
    fprintf((FILE *)(_iob_exref + 0x40),s_Bgn__4d_End__4d_1003f3ac,iVar2,iVar1);
    fprintf((FILE *)(_iob_exref + 0x40),s_RBgn__4d_REnd__4d_1003f3c0,local_10,local_18);
  }
  return;
}

//===== 0x1000d1fa =====

/* public: void __thiscall CSIBQWrap::getMajorMinor(int &,int &,char const * *)const  */

void __thiscall CSIBQWrap::getMajorMinor(CSIBQWrap *this,int *param_1,int *param_2,char **param_3)

{
                    /* 0xd1fa  191  ?getMajorMinor@CSIBQWrap@@QBEXAAH0PAPBD@Z */
  FUN_1000d3c0(*(void **)this,(StsMajor *)param_1,param_2,param_3);
  return;
}

//===== 0x1000d220 =====

void * __thiscall FUN_1000d220(void *this,uint param_1)

{
  FUN_1000d6c6((int)this);
  if ((param_1 & 1) != 0) {
    operator_delete(this);
  }
  return this;
}

//===== 0x1000d250 =====

int __fastcall FUN_1000d250(int param_1)

{
  return param_1 + 0xd0;
}

//===== 0x1000d270 =====

int __fastcall FUN_1000d270(int param_1)

{
  return param_1 + 0x3d8;
}

//===== 0x1000d290 =====

undefined4 __fastcall FUN_1000d290(int param_1)

{
  return *(undefined4 *)(param_1 + 0x6e0);
}

//===== 0x1000d2b0 =====

uint __thiscall FUN_1000d2b0(void *this,uint param_1)

{
  return *(uint *)((int)this + 0x28) & param_1;
}

//===== 0x1000d2d0 =====

void FUN_1000d2d0(Wvfm *param_1)

{
  Wvfm::rows(param_1);
  return;
}

//===== 0x1000d2f0 =====

int __fastcall FUN_1000d2f0(int param_1)

{
  return param_1 + 0x40;
}

//===== 0x1000d310 =====

undefined4 __fastcall FUN_1000d310(int param_1)

{
  FUN_1000f143(param_1);
  return *(undefined4 *)(param_1 + 0x6e4);
}

//===== 0x1000d330 =====

int __fastcall FUN_1000d330(int param_1)

{
  return param_1 + 0x48;
}

//===== 0x1000d350 =====

int __fastcall FUN_1000d350(int param_1)

{
  return param_1 + 0x88;
}

//===== 0x1000d370 =====

int __fastcall FUN_1000d370(int param_1)

{
  return param_1 + 0x700;
}

//===== 0x1000d390 =====

void __thiscall FUN_1000d390(void *this,int *param_1,int *param_2)

{
  Wvfm::getRawBgnEndPts((Wvfm *)((int)this + 0xd0),param_1,param_2);
  return;
}

//===== 0x1000d3c0 =====

void __thiscall FUN_1000d3c0(void *this,StsMajor *param_1,int *param_2,char **param_3)

{
  StsMajor local_8;
  
  Wvfm::majorMinorCode((Wvfm *)((int)this + 0xd0),&local_8,param_2,param_3);
  *param_1 = local_8;
  return;
}

//===== 0x1000d400 =====

bool __thiscall FUN_1000d400(void *this,int param_1,int param_2)

{
  *(int *)((int)this + 0xc) = param_1;
  *(int *)((int)this + 0x10) = param_2;
  *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) | 4;
  return *(int *)this != 2;
}

//===== 0x1000d440 =====

bool __thiscall FUN_1000d440(void *this,int param_1,int param_2,int param_3,int param_4,int param_5)

{
  *(int *)((int)this + 0x14) = param_1;
  *(int *)((int)this + 0x18) = param_2;
  *(int *)((int)this + 0x1c) = param_3;
  *(int *)((int)this + 0x20) = param_4;
  *(int *)((int)this + 0x24) = param_5;
  *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) | 0x20;
  return *(int *)this != 2;
}

//===== 0x1000d4a0 =====

void __thiscall FUN_1000d4a0(void *this,int param_1)

{
  FUN_1000dede(this,param_1);
  return;
}

//===== 0x1000d4c0 =====

void __thiscall FUN_1000d4c0(void *this,undefined4 param_1)

{
  *(undefined4 *)((int)this + 0x700) = param_1;
  return;
}

//===== 0x1000d4e0 =====

undefined4 * __fastcall FUN_1000d4e0(undefined4 *param_1)

{
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036f1f;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *param_1 = 0;
  param_1[1] = 0;
  param_1[2] = 0;
  param_1[3] = 0;
  param_1[4] = 0;
  param_1[5] = 1;
  param_1[6] = 1;
  param_1[7] = 0;
  param_1[8] = 1;
  param_1[9] = 0;
  param_1[10] = 0;
  param_1[0xb] = 0;
  param_1[0x32] = 0;
  Wvfm::Wvfm((Wvfm *)(param_1 + 0x34));
  local_8 = 0;
  Wvfm::Wvfm((Wvfm *)(param_1 + 0xf6));
  param_1[0x1b8] = 0;
  param_1[0x1b9] = 0;
  param_1[0x1ba] = 0;
  param_1[0x1bb] = 0;
  param_1[0x1bc] = 0;
  param_1[0x1bd] = 0;
  param_1[0x1be] = 0;
  param_1[0x1bf] = 0;
  param_1[0x1c1] = 0;
  memset(param_1 + 0x10,0,6);
  for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
    param_1[local_14 + 0xc] = local_14;
    for (local_18 = 0; local_18 < 4; local_18 = local_18 + 1) {
      param_1[local_14 * 4 + local_18 + 0x22] = 0;
      param_1[local_14 * 4 + local_18 + 0x12] = 0;
    }
  }
  param_1[0x1c0] = DAT_10038524;
  ExceptionList = local_10;
  return param_1;
}

//===== 0x1000d6c6 =====

void __fastcall FUN_1000d6c6(int param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_10036f47;
  local_10 = ExceptionList;
  local_8 = 1;
  ExceptionList = &local_10;
  FUN_1000d726(param_1);
  local_8 = local_8 & 0xffffff00;
  Wvfm::~Wvfm((Wvfm *)(param_1 + 0x3d8));
  local_8 = 0xffffffff;
  Wvfm::~Wvfm((Wvfm *)(param_1 + 0xd0));
  ExceptionList = local_10;
  return;
}

//===== 0x1000d726 =====

void __fastcall FUN_1000d726(int param_1)

{
  if (*(int *)(param_1 + 200) != 0) {
    operator_delete(*(void **)(param_1 + 200));
    *(undefined4 *)(param_1 + 0x2c) = 0;
    *(undefined4 *)(param_1 + 200) = 0;
  }
  if (*(int *)(param_1 + 0x6e0) != 0) {
    if (*(void **)(param_1 + 0x6e0) != (void *)0x0) {
      FUN_1000f6d0(*(void **)(param_1 + 0x6e0),1);
    }
    *(undefined4 *)(param_1 + 0x6e0) = 0;
  }
  if (*(int *)(param_1 + 0x6e8) != 0) {
    operator_delete(*(void **)(param_1 + 0x6e8));
    *(undefined4 *)(param_1 + 0x6e8) = 0;
  }
  if (*(int *)(param_1 + 0x6ec) != 0) {
    operator_delete(*(void **)(param_1 + 0x6ec));
    *(undefined4 *)(param_1 + 0x6ec) = 0;
  }
  if (*(int *)(param_1 + 0x6f0) != 0) {
    operator_delete(*(void **)(param_1 + 0x6f0));
    *(undefined4 *)(param_1 + 0x6f0) = 0;
  }
  if (*(int *)(param_1 + 0x6f4) != 0) {
    operator_delete(*(void **)(param_1 + 0x6f4));
    *(undefined4 *)(param_1 + 0x6f4) = 0;
  }
  if (*(int *)(param_1 + 0x6fc) != 0) {
    *(undefined4 *)(param_1 + 0x6f8) = 0;
    operator_delete(*(void **)(param_1 + 0x6fc));
    *(undefined4 *)(param_1 + 0x6fc) = 0;
  }
  if (*(int *)(param_1 + 0x704) != 0) {
    operator_delete(*(void **)(param_1 + 0x704));
    *(undefined4 *)(param_1 + 0x704) = 0;
  }
  *(undefined4 *)(param_1 + 0x6e4) = 0;
  return;
}

//===== 0x1000d8f5 =====

undefined4 * __thiscall FUN_1000d8f5(void *this,undefined4 *param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036f6f;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0xc) = 0;
  *(undefined4 *)((int)this + 0x10) = 0;
  *(undefined4 *)((int)this + 0x14) = 1;
  *(undefined4 *)((int)this + 0x18) = 1;
  *(undefined4 *)((int)this + 0x1c) = 0;
  *(undefined4 *)((int)this + 0x20) = 1;
  *(undefined4 *)((int)this + 0x24) = 0;
  *(undefined4 *)((int)this + 0x28) = 0;
  *(undefined4 *)((int)this + 0x2c) = 0;
  *(undefined4 *)((int)this + 200) = 0;
  Wvfm::Wvfm((Wvfm *)((int)this + 0xd0));
  local_8 = 0;
  Wvfm::Wvfm((Wvfm *)((int)this + 0x3d8));
  local_8 = CONCAT31(local_8._1_3_,1);
  *(undefined4 *)((int)this + 0x6e0) = 0;
  *(undefined4 *)((int)this + 0x6e4) = 0;
  *(undefined4 *)((int)this + 0x6e8) = 0;
  *(undefined4 *)((int)this + 0x6ec) = 0;
  *(undefined4 *)((int)this + 0x6f0) = 0;
  *(undefined4 *)((int)this + 0x6f4) = 0;
  *(undefined4 *)((int)this + 0x6f8) = 0;
  *(undefined4 *)((int)this + 0x6fc) = 0;
  *(undefined4 *)((int)this + 0x704) = 0;
  FUN_1000da57(this,param_1);
  ExceptionList = local_10;
  return this;
}

//===== 0x1000da57 =====

undefined4 * __thiscall FUN_1000da57(void *this,undefined4 *param_1)

{
  void *pvVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  int local_8;
  
  if (param_1 != this) {
    FUN_1000d726((int)this);
    *(undefined4 *)this = *param_1;
    *(undefined4 *)((int)this + 4) = param_1[1];
    *(undefined4 *)((int)this + 8) = param_1[2];
    *(undefined4 *)((int)this + 0xc) = param_1[3];
    *(undefined4 *)((int)this + 0x10) = param_1[4];
    *(undefined4 *)((int)this + 0x14) = param_1[5];
    *(undefined4 *)((int)this + 0x18) = param_1[6];
    *(undefined4 *)((int)this + 0x1c) = param_1[7];
    *(undefined4 *)((int)this + 0x20) = param_1[8];
    *(undefined4 *)((int)this + 0x24) = param_1[9];
    *(undefined4 *)((int)this + 0x28) = param_1[10];
    memcpy((void *)((int)this + 0x40),param_1 + 0x10,6);
    RdrOut::operator=(*(RdrOut **)((int)this + 0x6e0),(RdrOut *)param_1[0x1b8]);
    Wvfm::operator=((Wvfm *)((int)this + 0xd0),(Wvfm *)(param_1 + 0x34));
    Wvfm::operator=((Wvfm *)((int)this + 0x3d8),(Wvfm *)(param_1 + 0xf6));
    *(undefined4 *)((int)this + 0x2c) = param_1[0xb];
    pvVar1 = operator_new(*(int *)((int)this + 0x2c) << 4);
    *(void **)((int)this + 200) = pvVar1;
    if (*(int *)((int)this + 200) == 0) {
      FUN_1000dede(this,1);
    }
    else {
      for (local_8 = 0; local_8 < *(int *)((int)this + 0x2c); local_8 = local_8 + 1) {
        puVar3 = (undefined4 *)(param_1[0x32] + local_8 * 0x10);
        puVar2 = (undefined4 *)(*(int *)((int)this + 200) + local_8 * 0x10);
        *puVar2 = *puVar3;
        puVar2[1] = puVar3[1];
        puVar2[2] = puVar3[2];
        puVar2[3] = puVar3[3];
      }
      for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
        *(undefined4 *)((int)this + local_8 * 4 + 0x30) = param_1[local_8 + 0xc];
        puVar2 = param_1 + local_8 * 4 + 0x12;
        puVar3 = (undefined4 *)((int)this + local_8 * 0x10 + 0x48);
        *puVar3 = *puVar2;
        puVar3[1] = puVar2[1];
        puVar3[2] = puVar2[2];
        puVar3[3] = puVar2[3];
        puVar2 = param_1 + local_8 * 4 + 0x22;
        puVar3 = (undefined4 *)((int)this + local_8 * 0x10 + 0x88);
        *puVar3 = *puVar2;
        puVar3[1] = puVar2[1];
        puVar3[2] = puVar2[2];
        puVar3[3] = puVar2[3];
      }
    }
    *(undefined4 *)((int)this + 0x6e4) = param_1[0x1b9];
    if (*(int *)((int)this + 0x6e4) != 0) {
      pvVar1 = operator_new(*(uint *)((int)this + 0x6e4));
      *(void **)((int)this + 0x6e8) = pvVar1;
      pvVar1 = operator_new(*(uint *)((int)this + 0x6e4));
      *(void **)((int)this + 0x6ec) = pvVar1;
      pvVar1 = operator_new(*(int *)((int)this + 0x6e4) << 2);
      *(void **)((int)this + 0x6f0) = pvVar1;
      pvVar1 = operator_new(*(int *)((int)this + 0x6e4) << 2);
      *(void **)((int)this + 0x6f4) = pvVar1;
      pvVar1 = operator_new(*(int *)((int)this + 0x6e4) << 4);
      *(void **)((int)this + 0x704) = pvVar1;
      for (local_8 = 0; local_8 < *(int *)((int)this + 0x6e4); local_8 = local_8 + 1) {
        *(undefined1 *)(*(int *)((int)this + 0x6e8) + local_8) =
             *(undefined1 *)(param_1[0x1ba] + local_8);
        *(undefined1 *)(*(int *)((int)this + 0x6ec) + local_8) =
             *(undefined1 *)(param_1[0x1bb] + local_8);
        *(undefined4 *)(*(int *)((int)this + 0x6f0) + local_8 * 4) =
             *(undefined4 *)(param_1[0x1bc] + local_8 * 4);
        *(undefined4 *)(*(int *)((int)this + 0x6f4) + local_8 * 4) =
             *(undefined4 *)(param_1[0x1bd] + local_8 * 4);
        puVar2 = (undefined4 *)(param_1[0x1c1] + local_8 * 0x10);
        puVar3 = (undefined4 *)(*(int *)((int)this + 0x704) + local_8 * 0x10);
        *puVar3 = *puVar2;
        puVar3[1] = puVar2[1];
        puVar3[2] = puVar2[2];
        puVar3[3] = puVar2[3];
      }
    }
    *(undefined4 *)((int)this + 0x6f8) = param_1[0x1be];
    if (*(int *)((int)this + 0x6f8) != 0) {
      pvVar1 = operator_new(*(int *)((int)this + 0x6f8) * 4 + 8);
      *(void **)((int)this + 0x6fc) = pvVar1;
      for (local_8 = 0; local_8 < *(int *)((int)this + 0x6f8); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)((int)this + 0x6fc) + local_8 * 4) =
             *(undefined4 *)(param_1[0x1bf] + local_8 * 4);
      }
    }
    *(undefined4 *)((int)this + 0x700) = param_1[0x1c0];
  }
  return this;
}

//===== 0x1000dead =====

void FUN_1000dead(void)

{
  FUN_1000deb7();
  return;
}

//===== 0x1000deb7 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1000deb7(void)

{
  _DAT_10041d00 = acos(-1.0);
  return;
}

//===== 0x1000ded1 =====

undefined4 FUN_1000ded1(void)

{
  return 0;
}

//===== 0x1000dede =====

bool __thiscall FUN_1000dede(void *this,int param_1)

{
  if ((*(int *)this != 2) || (param_1 == 2)) {
    *(int *)this = param_1;
  }
  return *(int *)this != 2;
}

//===== 0x1000df0e =====

bool __thiscall FUN_1000df0e(void *this,int param_1,int param_2)

{
  void *pvVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  bool bVar4;
  int local_c;
  
  *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) & 0xfffffffe;
  if (*(int *)((int)this + 200) != 0) {
    operator_delete(*(void **)((int)this + 200));
    *(undefined4 *)((int)this + 200) = 0;
  }
  *(int *)((int)this + 0x2c) = param_2;
  pvVar1 = operator_new((*(int *)((int)this + 0x2c) + 2) * 0x10);
  *(void **)((int)this + 200) = pvVar1;
  if (*(int *)((int)this + 200) == 0) {
    FUN_1000dede(this,1);
    bVar4 = false;
  }
  else {
    for (local_c = 0; local_c < *(int *)((int)this + 0x2c); local_c = local_c + 1) {
      puVar3 = (undefined4 *)(param_1 + local_c * 0x10);
      puVar2 = (undefined4 *)(*(int *)((int)this + 200) + local_c * 0x10);
      *puVar2 = *puVar3;
      puVar2[1] = puVar3[1];
      puVar2[2] = puVar3[2];
      puVar2[3] = puVar3[3];
    }
    *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) | 1;
    if ((*(uint *)((int)this + 0x28) & 3) == 3) {
      FUN_1000dede(this,3);
    }
    bVar4 = *(int *)this != 2;
  }
  return bVar4;
}

//===== 0x1000e02e =====

bool __thiscall FUN_1000e02e(void *this,int param_1,int param_2)

{
  void *pvVar1;
  bool bVar2;
  undefined4 local_c;
  
  *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) & 0xfffffeff;
  if (*(int *)((int)this + 0x6fc) != 0) {
    operator_delete(*(void **)((int)this + 0x6fc));
    *(undefined4 *)((int)this + 0x6fc) = 0;
  }
  *(int *)((int)this + 0x6f8) = param_2;
  pvVar1 = operator_new(*(int *)((int)this + 0x6f8) * 4 + 8);
  *(void **)((int)this + 0x6fc) = pvVar1;
  if (*(int *)((int)this + 0x6fc) == 0) {
    FUN_1000dede(this,1);
    bVar2 = false;
  }
  else {
    for (local_c = 0; local_c < *(int *)((int)this + 0x6f8); local_c = local_c + 1) {
      *(undefined4 *)(*(int *)((int)this + 0x6fc) + local_c * 4) =
           *(undefined4 *)(param_1 + local_c * 4);
    }
    *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) | 0x100;
    bVar2 = *(int *)this != 2;
  }
  return bVar2;
}

//===== 0x1000e123 =====

int __fastcall FUN_1000e123(int *param_1)

{
  RdrOut *this;
  int local_30;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036f84;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  local_14 = FUN_1000e4f3(param_1);
  if (local_14 != 0) {
    if ((param_1[0x1b8] != 0) && ((void *)param_1[0x1b8] != (void *)0x0)) {
      FUN_1000f6d0((void *)param_1[0x1b8],1);
    }
    this = operator_new(0x4e8);
    local_8 = 0;
    if (this == (RdrOut *)0x0) {
      local_30 = 0;
    }
    else {
      local_30 = RdrOut::RdrOut(this,(Wvfm *)(param_1 + 0x34));
    }
    local_8 = 0xffffffff;
    param_1[0x1b8] = local_30;
    if (param_1[0x1b8] == 0) {
      FUN_1000dede(param_1,1);
    }
    else {
      local_14 = Wvfm::nfeeder((Wvfm *)(param_1 + 0x34),(RdrOut *)param_1[0x1b8],
                               (TestOptions *)(param_1 + 0x1c0),1);
      if (local_14 == 1) {
        RdrOut::Edit((RdrOut *)param_1[0x1b8],(char *)0x0);
        RdrOut::Beautify((RdrOut *)param_1[0x1b8],param_1[5],param_1[6],param_1[7],param_1[8],
                         param_1[9]);
        param_1[10] = param_1[10] | 0x40;
        FUN_1000e8d4(param_1);
      }
      else {
        FUN_1000f508(param_1);
      }
    }
  }
  ExceptionList = local_10;
  return local_14;
}

//===== 0x1000e29e =====

void __thiscall FUN_1000e29e(void *this,RdrOut *param_1)

{
  RdrOut *this_00;
  undefined4 local_2c;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036f99;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  if ((*(int *)((int)this + 0x6e0) != 0) &&
     (ExceptionList = &local_10, *(void **)((int)this + 0x6e0) != (void *)0x0)) {
    ExceptionList = &local_10;
    FUN_1000f6d0(*(void **)((int)this + 0x6e0),1);
  }
  this_00 = operator_new(0x4e8);
  local_8 = 0;
  if (this_00 == (RdrOut *)0x0) {
    local_2c = 0;
  }
  else {
    local_2c = RdrOut::RdrOut(this_00);
  }
  local_8 = 0xffffffff;
  *(undefined4 *)((int)this + 0x6e0) = local_2c;
  if (*(int *)((int)this + 0x6e0) == 0) {
    FUN_1000dede(this,1);
  }
  else {
    RdrOut::operator=(*(RdrOut **)((int)this + 0x6e0),param_1);
  }
  ExceptionList = local_10;
  return;
}

//===== 0x1000e37a =====

bool __thiscall FUN_1000e37a(void *this,char *param_1)

{
  strcpy((char *)((int)this + 0x40),param_1);
  *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) | 2;
  if ((*(uint *)((int)this + 0x28) & 3) == 3) {
    FUN_1000dede(this,3);
  }
  return *(int *)this != 2;
}

//===== 0x1000e3cb =====

void __thiscall FUN_1000e3cb(void *this,int param_1)

{
  Wvfm::annotate((Wvfm *)((int)this + 0xd0),param_1);
  return;
}

//===== 0x1000e3ea =====

bool __thiscall FUN_1000e3ea(void *this,int param_1)

{
  int local_c;
  int local_8;
  
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      *(undefined4 *)((int)this + local_c * 4 + local_8 * 0x10 + 0x48) =
           *(undefined4 *)(param_1 + local_8 * 0x10 + local_c * 4);
    }
  }
  *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) | 8;
  return *(int *)this != 2;
}

//===== 0x1000e46d =====

bool __thiscall FUN_1000e46d(void *this,int param_1)

{
  int local_c;
  int local_8;
  
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      *(undefined4 *)((int)this + local_c * 4 + local_8 * 0x10 + 0x88) =
           *(undefined4 *)(param_1 + local_8 * 0x10 + local_c * 4);
    }
  }
  *(uint *)((int)this + 0x28) = *(uint *)((int)this + 0x28) | 0x10;
  return *(int *)this != 2;
}

//===== 0x1000e4f3 =====

int __fastcall FUN_1000e4f3(int *param_1)

{
  int iVar1;
  int iVar2;
  int local_90 [16];
  int local_50;
  int local_4c [16];
  int local_c;
  int local_8;
  
  local_50 = 0;
  if ((param_1[10] & 3U) == 3) {
    if (*param_1 == 2) {
      local_50 = 0;
    }
    else {
      FUN_1000dede(param_1,3);
      param_1[10] = param_1[10] & 0xffffff7f;
      iVar2 = strncmp((char *)(param_1 + 0x10),PTR_s_ACTG__1003f424,4);
      if (iVar2 != 0) {
        for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
          for (local_c = 0; local_c < 4; local_c = local_c + 1) {
            iVar2 = toupper((int)*(char *)((int)param_1 + local_c + 0x40));
            if (iVar2 == (char)PTR_s_ACTG__1003f424[local_8]) {
              param_1[local_c + 0xc] = local_8;
              break;
            }
          }
        }
        param_1[10] = param_1[10] | 0x80;
      }
      for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
        iVar2 = param_1[local_8 + 0xc];
        for (local_c = 0; local_c < 4; local_c = local_c + 1) {
          iVar1 = param_1[local_c + 0xc];
          local_90[iVar2 * 4 + iVar1] = param_1[local_8 * 4 + local_c + 0x12];
          local_4c[iVar2 * 4 + iVar1] = param_1[local_8 * 4 + local_c + 0x22];
        }
      }
      iVar2 = Wvfm::dim((Wvfm *)(param_1 + 0x34),param_1[0xb]);
      local_50 = 0;
      if (iVar2 != 0) {
        local_50 = iVar2;
        Wvfm::ds((Wvfm *)(param_1 + 0x34),param_1[1]);
        local_50 = Wvfm::licenseOk((Wvfm *)(param_1 + 0x34));
        if (local_50 == 0) {
          FUN_1000f508(param_1);
        }
        else {
          for (local_8 = 1; local_8 <= param_1[0xb]; local_8 = local_8 + 1) {
            for (local_c = 1; local_c < 5; local_c = local_c + 1) {
              Wvfm::sc_la_set((Wvfm *)(param_1 + 0x34),local_8,param_1[local_c + 0xb] + 1,
                              (double)*(float *)(param_1[0x32] + (local_8 + -1) * 0x10 + -4 +
                                                local_c * 4));
            }
          }
          Wvfm::smplRate((Wvfm *)(param_1 + 0x34),2);
          Wvfm::lnordr((Wvfm *)(param_1 + 0x34),PTR_s_ACTG__1003f424);
          if ((param_1[10] & 4U) != 0) {
            FUN_1000ed13(param_1,(Wvfm *)(param_1 + 0x34));
          }
          if ((param_1[10] & 8U) != 0) {
            FUN_1000ed3e((Wvfm *)(param_1 + 0x34),(int)local_90);
          }
          if ((param_1[10] & 0x10U) != 0) {
            FUN_1000ee2f((Wvfm *)(param_1 + 0x34),(int)local_4c);
          }
          if (((param_1[10] & 0x100U) != 0) && (param_1[0x1bf] != 0)) {
            for (local_8 = 1; local_8 <= param_1[0x1be]; local_8 = local_8 + 1) {
              Wvfm::setCurr((Wvfm *)(param_1 + 0x34),local_8,
                            *(float *)(param_1[0x1bf] + -4 + local_8 * 4));
            }
          }
        }
      }
    }
  }
  else {
    local_50 = 0;
  }
  return local_50;
}

//===== 0x1000e8d4 =====

undefined4 __fastcall FUN_1000e8d4(int *param_1)

{
  undefined4 uVar1;
  int iVar2;
  double dVar3;
  float local_108 [4];
  float local_f8 [4];
  double local_e8 [4];
  int local_c8;
  int local_c4;
  Wvfm *local_c0;
  float local_bc [4];
  int local_ac [16];
  Annotate *local_6c;
  float local_68 [4];
  BandStatArray *local_58;
  int local_54 [16];
  int local_14;
  float local_10;
  int local_c;
  int local_8;
  
  local_c0 = RdrOut::wvfm((RdrOut *)param_1[0x1b8]);
  local_6c = Wvfm::getAnnotation(local_c0);
  if (*param_1 == 2) {
    uVar1 = 0;
  }
  else {
    iVar2 = Wvfm::rows(local_c0);
    param_1[0xb] = iVar2;
    FUN_1000edc0(local_c0,(int)(param_1 + 0x12));
    FUN_1000eecf(local_c0,(int)(param_1 + 0x22));
    if ((param_1[10] & 0x80U) == 0) {
      uVar1 = 1;
    }
    else {
      iVar2 = strncmp((char *)(param_1 + 0x10),PTR_s_ACTG__1003f424,4);
      if (iVar2 != 0) {
        for (local_c = 0; local_c < 4; local_c = local_c + 1) {
          for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
            iVar2 = toupper((int)*(char *)((int)param_1 + local_14 + 0x40));
            if (iVar2 == (char)PTR_s_ACTG__1003f424[local_c]) {
              param_1[local_c + 0xc] = local_14;
              break;
            }
          }
        }
      }
      Wvfm::lnordr(local_c0,(char *)(param_1 + 0x10));
      FUN_1000edc0(local_c0,(int)local_ac);
      FUN_1000eecf(local_c0,(int)local_54);
      if (local_6c != (Annotate *)0x0) {
        Annotate::getSpecSepQual(local_6c,&local_10,local_bc);
        for (local_c = 0; local_c < 4; local_c = local_c + 1) {
          local_68[param_1[local_c + 0xc]] = local_bc[local_c];
        }
        Annotate::setSpecSepQual(local_6c,local_10,local_68);
      }
      for (local_c = 0; local_c < 4; local_c = local_c + 1) {
        local_c4 = param_1[local_c + 0xc];
        for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
          local_c8 = param_1[local_14 + 0xc];
          param_1[local_c4 * 4 + local_c8 + 0x12] = local_ac[local_c * 4 + local_14];
          param_1[local_c4 * 4 + local_c8 + 0x22] = local_54[local_c * 4 + local_14];
        }
      }
      FUN_1000ed3e(local_c0,(int)(param_1 + 0x12));
      FUN_1000ee2f(local_c0,(int)(param_1 + 0x22));
      for (local_c = 1; local_c <= param_1[0xb]; local_c = local_c + 1) {
        for (local_14 = 1; local_14 < 5; local_14 = local_14 + 1) {
          dVar3 = Wvfm::sc_la(local_c0,local_c,local_14);
          local_e8[param_1[local_14 + 0xb]] = dVar3;
        }
        for (local_14 = 1; local_14 < 5; local_14 = local_14 + 1) {
          Wvfm::sc_la_set(local_c0,local_c,local_14,
                          (double)CONCAT44(*(undefined4 *)((int)local_e8 + local_14 * 8 + -4),
                                           *(undefined4 *)(local_e8 + local_14 + -1)));
        }
      }
      local_58 = RdrOut::bandstat((RdrOut *)param_1[0x1b8]);
      local_8 = Wvfm::annotate((Wvfm *)local_58);
      for (local_c = 0; local_c < local_8; local_c = local_c + 1) {
        BandStatArray::quad(local_58,local_c,local_108);
        for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
          local_f8[param_1[local_14 + 0xc]] = local_108[local_14];
        }
        BandStatArray::squad(local_58,local_c,local_f8);
      }
      param_1[10] = param_1[10] & 0xffffff7f;
      uVar1 = 1;
    }
  }
  return uVar1;
}

//===== 0x1000ed13 =====

void __thiscall FUN_1000ed13(void *this,Wvfm *param_1)

{
  Wvfm::bgni(param_1,*(int *)((int)this + 0xc));
  Wvfm::endi(param_1,*(int *)((int)this + 0x10));
  return;
}

//===== 0x1000ed3e =====

void FUN_1000ed3e(Wvfm *param_1,int param_2)

{
  int local_5c;
  SSTLUT local_58 [16];
  char acStack_48 [64];
  int local_8;
  
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    acStack_48[local_8 * 0x14] = (char)local_8 + '\x01';
    for (local_5c = 0; local_5c < 4; local_5c = local_5c + 1) {
      *(undefined4 *)(local_58 + local_5c * 4 + local_8 * 0x14) =
           *(undefined4 *)(param_2 + local_8 * 0x10 + local_5c * 4);
    }
  }
  Wvfm::setSSTPattern(param_1,local_58);
  return;
}

//===== 0x1000edc0 =====

void FUN_1000edc0(Wvfm *param_1,int param_2)

{
  ObsInpSpec *this;
  float fVar1;
  undefined4 local_10;
  undefined4 local_8;
  
  this = Wvfm::ispec(param_1);
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    for (local_10 = 0; local_10 < 4; local_10 = local_10 + 1) {
      fVar1 = ObsInpSpec::xtalk(this,local_8,local_10);
      *(float *)(param_2 + local_8 * 0x10 + local_10 * 4) = fVar1;
    }
  }
  return;
}

//===== 0x1000ee2f =====

void FUN_1000ee2f(Wvfm *param_1,int param_2)

{
  int local_90;
  int local_8c;
  double local_88 [16];
  int local_8;
  
  local_8c = 0;
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    for (local_90 = 0; local_90 < 4; local_90 = local_90 + 1) {
      local_88[local_8c] = (double)*(float *)(param_2 + local_8 * 0x10 + local_90 * 4);
      local_8c = local_8c + 1;
    }
  }
  Wvfm::ssm(param_1,local_88,0);
  return;
}

//===== 0x1000eecf =====

void FUN_1000eecf(Wvfm *param_1,int param_2)

{
  double *pdVar1;
  int local_10;
  int local_c;
  
  pdVar1 = Wvfm::ssm(param_1);
  for (local_c = 0; local_c < 4; local_c = local_c + 1) {
    for (local_10 = 0; local_10 < 4; local_10 = local_10 + 1) {
      *(float *)(param_2 + local_c * 0x10 + local_10 * 4) = (float)pdVar1[local_10 + local_c * 4];
    }
  }
  return;
}

//===== 0x1000ef40 =====

undefined4 FUN_1000ef40(Wvfm *param_1,int param_2,int param_3)

{
  Status SVar1;
  double dVar2;
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  
  local_8 = 0;
  SVar1 = Wvfm::status(param_1);
  if ((SVar1 == 1) && (param_2 != 0)) {
    for (local_c = 0; local_c < param_3; local_c = local_c + 1) {
      for (local_10 = 0; local_10 < 4; local_10 = local_10 + 1) {
        dVar2 = Wvfm::sc_la(param_1,local_c + 1,local_10 + 1);
        *(float *)(param_2 + local_c * 0x10 + local_10 * 4) = (float)dVar2;
      }
    }
    local_8 = 1;
  }
  return local_8;
}

//===== 0x1000efd3 =====

undefined4 FUN_1000efd3(Wvfm *param_1,int param_2,int param_3)

{
  Status SVar1;
  float fVar2;
  undefined4 local_c;
  undefined4 local_8;
  
  local_8 = 0;
  SVar1 = Wvfm::status(param_1);
  if ((SVar1 == 1) && (param_2 != 0)) {
    for (local_c = 0; local_c < param_3; local_c = local_c + 1) {
      fVar2 = Wvfm::getCurr(param_1,local_c + 1);
      *(float *)(param_2 + local_c * 4) = fVar2;
    }
    local_8 = 1;
  }
  return local_8;
}

//===== 0x1000f03a =====

int __fastcall FUN_1000f03a(int *param_1)

{
  int local_c;
  
  FUN_1000f143((int)param_1);
  if (*param_1 == 2) {
    local_c = 0;
  }
  else {
    local_c = param_1[0x1ba];
  }
  return local_c;
}

//===== 0x1000f06f =====

int __fastcall FUN_1000f06f(int *param_1)

{
  int local_c;
  
  FUN_1000f143((int)param_1);
  if (*param_1 == 2) {
    local_c = 0;
  }
  else {
    local_c = param_1[0x1bb];
  }
  return local_c;
}

//===== 0x1000f0a4 =====

int __fastcall FUN_1000f0a4(int *param_1)

{
  int local_c;
  
  FUN_1000f143((int)param_1);
  if (*param_1 == 2) {
    local_c = 0;
  }
  else {
    local_c = param_1[0x1c1];
  }
  return local_c;
}

//===== 0x1000f0d9 =====

int __fastcall FUN_1000f0d9(int *param_1)

{
  int local_c;
  
  FUN_1000f143((int)param_1);
  if (*param_1 == 2) {
    local_c = 0;
  }
  else {
    local_c = param_1[0x1bc];
  }
  return local_c;
}

//===== 0x1000f10e =====

int __fastcall FUN_1000f10e(int *param_1)

{
  int local_c;
  
  FUN_1000f143((int)param_1);
  if (*param_1 == 2) {
    local_c = 0;
  }
  else {
    local_c = param_1[0x1bd];
  }
  return local_c;
}

//===== 0x1000f143 =====

void __fastcall FUN_1000f143(int param_1)

{
  char cVar1;
  RdrOut *pRVar2;
  BandStatArray *pBVar3;
  int iVar4;
  void *pvVar5;
  float fVar6;
  undefined4 local_c;
  
  if (*(int *)(param_1 + 0x6e4) == 0) {
    pRVar2 = (RdrOut *)FUN_1000d290(param_1);
    pBVar3 = RdrOut::bandstat(pRVar2);
    iVar4 = Wvfm::annotate((Wvfm *)pBVar3);
    *(int *)(param_1 + 0x6e4) = iVar4;
    pRVar2 = (RdrOut *)FUN_1000d290(param_1);
    iVar4 = RdrOut::getXOverCut(pRVar2);
    if (iVar4 != 0) {
      *(int *)(param_1 + 0x6e4) = iVar4;
    }
    if (0 < *(int *)(param_1 + 0x6e4)) {
      pRVar2 = (RdrOut *)FUN_1000d290(param_1);
      pBVar3 = RdrOut::bandstat(pRVar2);
      pvVar5 = operator_new(*(int *)(param_1 + 0x6e4) + 1);
      *(void **)(param_1 + 0x6e8) = pvVar5;
      pvVar5 = operator_new(*(int *)(param_1 + 0x6e4) + 1);
      *(void **)(param_1 + 0x6ec) = pvVar5;
      pvVar5 = operator_new(*(int *)(param_1 + 0x6e4) * 4 + 4);
      *(void **)(param_1 + 0x6f0) = pvVar5;
      pvVar5 = operator_new(*(int *)(param_1 + 0x6e4) * 4 + 4);
      *(void **)(param_1 + 0x6f4) = pvVar5;
      pvVar5 = operator_new((*(int *)(param_1 + 0x6e4) + 1) * 0x10);
      *(void **)(param_1 + 0x704) = pvVar5;
      for (local_c = 0; local_c < *(int *)(param_1 + 0x6e4); local_c = local_c + 1) {
        cVar1 = BandStatArray::call(pBVar3,local_c);
        *(char *)(*(int *)(param_1 + 0x6e8) + local_c) = cVar1;
        cVar1 = BandStatArray::iubc(pBVar3,local_c);
        *(char *)(*(int *)(param_1 + 0x6ec) + local_c) = cVar1;
        BandStatArray::quad(pBVar3,local_c,(float *)(*(int *)(param_1 + 0x704) + local_c * 0x10));
        iVar4 = BandStatArray::posn(pBVar3,local_c);
        *(int *)(*(int *)(param_1 + 0x6f0) + local_c * 4) = iVar4;
        fVar6 = BandStatArray::qual(pBVar3,local_c);
        *(float *)(*(int *)(param_1 + 0x6f4) + local_c * 4) = fVar6;
      }
      *(undefined1 *)(*(int *)(param_1 + 0x6e8) + local_c) = 0;
      *(undefined1 *)(*(int *)(param_1 + 0x6ec) + local_c) = 0;
    }
  }
  return;
}

//===== 0x1000f339 =====

int __fastcall FUN_1000f339(int *param_1)

{
  int iVar1;
  int local_10;
  int local_c;
  
  if ((param_1[10] & 1U | 2) == 3) {
    if (*param_1 == 2) {
      iVar1 = 0;
    }
    else {
      iVar1 = Wvfm::dim((Wvfm *)(param_1 + 0xf6),param_1[0xb]);
      if (iVar1 != 0) {
        Wvfm::ds((Wvfm *)(param_1 + 0xf6),param_1[1]);
        for (local_c = 1; local_c <= param_1[0xb]; local_c = local_c + 1) {
          for (local_10 = 1; local_10 < 5; local_10 = local_10 + 1) {
            Wvfm::sc_la_set((Wvfm *)(param_1 + 0xf6),local_c,local_10,
                            (double)*(float *)(param_1[0x32] + (local_c + -1) * 0x10 + -4 +
                                              local_10 * 4));
          }
        }
        Wvfm::lnordr((Wvfm *)(param_1 + 0xf6),(char *)(param_1 + 0x10));
        Wvfm::smplRate((Wvfm *)(param_1 + 0xf6),2);
        if ((param_1[10] & 4U) != 0) {
          FUN_1000ed13(param_1,(Wvfm *)(param_1 + 0xf6));
        }
        if ((param_1[10] & 8U) != 0) {
          FUN_1000ed3e((Wvfm *)(param_1 + 0xf6),(int)(param_1 + 0x12));
        }
        if ((param_1[10] & 0x10U) != 0) {
          FUN_1000ee2f((Wvfm *)(param_1 + 0xf6),(int)(param_1 + 0x22));
        }
        if (((param_1[10] & 0x100U) != 0) && (param_1[0x1bf] != 0)) {
          for (local_c = 1; local_c <= param_1[0x1be]; local_c = local_c + 1) {
            Wvfm::setCurr((Wvfm *)(param_1 + 0xf6),local_c,
                          *(float *)(param_1[0x1bf] + -4 + local_c * 4));
          }
        }
      }
    }
  }
  else {
    iVar1 = 0;
  }
  return iVar1;
}

//===== 0x1000f508 =====

undefined4 __fastcall FUN_1000f508(undefined4 *param_1)

{
  Status SVar1;
  undefined4 local_8;
  
  SVar1 = Wvfm::status((Wvfm *)(param_1 + 0x34));
  switch(SVar1) {
  case 0:
    local_8 = 5;
    break;
  case 1:
    local_8 = 6;
    break;
  case 2:
    local_8 = 7;
    break;
  case 3:
    local_8 = 8;
    break;
  case 4:
    local_8 = 9;
    break;
  case 5:
    local_8 = 10;
    break;
  case 6:
    local_8 = 0xb;
    break;
  case 7:
    local_8 = 0xc;
    break;
  case 8:
    local_8 = 0xd;
    break;
  case 10:
    local_8 = 0xf;
    break;
  case 0xb:
    local_8 = 0x10;
    break;
  case 0xc:
    local_8 = 0x11;
    break;
  case 0xd:
    local_8 = 0x12;
    break;
  case 0xe:
    local_8 = 0x13;
    break;
  case 0xf:
    local_8 = 0x14;
    break;
  case 0x10:
    local_8 = 0x15;
    break;
  case 0x11:
    local_8 = 0x16;
    break;
  case 0x12:
    local_8 = 0x17;
    break;
  case 0x13:
    local_8 = 0x18;
    break;
  case 0x14:
    local_8 = 0x1c;
    break;
  case 0x15:
    local_8 = 0x19;
    break;
  case 0x16:
    local_8 = 0x1a;
    break;
  case 0x17:
    local_8 = 0x1b;
  }
  *param_1 = local_8;
  return local_8;
}

//===== 0x1000f690 =====

undefined * __fastcall FUN_1000f690(uint *param_1)

{
  undefined *local_c;
  
  if (*param_1 < 0x1e) {
    local_c = (&PTR_s_uninitilized_1003f430)[*param_1];
  }
  else {
    local_c = PTR_s_unknown_error_1003f4a4;
  }
  return local_c;
}

//===== 0x1000f6d0 =====

RdrOut * __thiscall FUN_1000f6d0(void *this,uint param_1)

{
  RdrOut::~RdrOut(this);
  if ((param_1 & 1) != 0) {
    operator_delete(this);
  }
  return this;
}

//===== 0x1000f700 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: int __thiscall Wvfm::decimateP(int) */

int __thiscall Wvfm::decimateP(Wvfm *this,int param_1)

{
  int iVar1;
  double *pdVar2;
  int iVar3;
  int iVar4;
  double **ppdVar5;
  float *pfVar6;
  undefined4 uVar7;
  int iVar8;
  double dVar9;
  float fVar10;
  float fVar11;
  ObsInpSpec *local_1d8;
  float local_1cc;
  int local_1c8;
  int local_1c4;
  int local_1b0;
  int local_1ac;
  int local_1a4;
  undefined4 local_188;
  undefined4 uStack_184;
  int local_17c;
  int local_178;
  int local_174;
  double local_170;
  float local_15c;
  int local_158;
  undefined8 uStack_14c;
  undefined8 local_144;
  double adStack_13c [3];
  float local_124;
  ObsInpSpec *local_120;
  int local_11c;
  undefined4 local_118;
  undefined4 uStack_114;
  undefined8 local_110;
  undefined4 local_108;
  int local_104;
  float local_100;
  int local_fc;
  ObsInpSpec local_f8 [232];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0xf700  135  ?decimateP@Wvfm@@AAEHH@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036fbc;
  local_10 = ExceptionList;
  local_178 = ((*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1) / 0x14;
  if (local_178 < 300) {
    local_178 = local_178 << 1;
  }
  iVar8 = *(int *)(this + 0xb8) + local_178;
  local_178 = iVar8 + local_178;
  local_108 = *(undefined4 *)(this + 0xbc);
  local_174 = 0;
  local_104 = 0;
  local_158 = 0;
  local_170 = 4.0;
  local_15c = 0.0;
  local_124 = 0.0;
  local_100 = 0.0;
  ExceptionList = &local_10;
  ObsInpSpec::ObsInpSpec(local_f8);
  local_8 = 0;
  if (param_1 == 0) {
    local_1d8 = local_f8;
  }
  else {
    local_1d8 = (ObsInpSpec *)(this + 0x210);
  }
  local_120 = local_1d8;
  ObsInpSpec::setMeasurementRange(local_1d8,iVar8,local_178);
  *(undefined4 *)(this + 0x1b0) = 0;
  for (local_17c = 1; local_17c < 5; local_17c = local_17c + 1) {
    iVar3 = *(int *)(*(int *)(this + 0xc4) + iVar8 * 4);
    *(undefined4 *)(&uStack_14c + local_17c) = *(undefined4 *)(iVar3 + local_17c * 8);
    *(undefined4 *)((int)&uStack_14c + local_17c * 8 + 4) =
         *(undefined4 *)(iVar3 + 4 + local_17c * 8);
    local_11c = iVar8;
    while (local_11c = local_11c + 1, local_11c <= local_178) {
      if (*(double *)(*(int *)(*(int *)(this + 0xc4) + local_11c * 4) + local_17c * 8) <
          (double)(&uStack_14c)[local_17c]) {
        iVar3 = *(int *)(*(int *)(this + 0xc4) + local_11c * 4);
        *(undefined4 *)(&uStack_14c + local_17c) = *(undefined4 *)(iVar3 + local_17c * 8);
        *(undefined4 *)((int)&uStack_14c + local_17c * 8 + 4) =
             *(undefined4 *)(iVar3 + 4 + local_17c * 8);
      }
    }
  }
  pdVar2 = dvector(1,local_178);
  for (local_11c = iVar8; local_11c <= local_178; local_11c = local_11c + 1) {
    pdVar2[local_11c] = *(double *)(*(int *)(*(int *)(this + 0xc4) + local_11c * 4) + 8) - local_144
    ;
    for (local_17c = 2; local_17c < 5; local_17c = local_17c + 1) {
      dVar9 = *(double *)(*(int *)(*(int *)(this + 0xc4) + local_11c * 4) + local_17c * 8) -
              (double)(&uStack_14c)[local_17c];
      if (pdVar2[local_11c] < dVar9) {
        local_188 = SUB84(dVar9,0);
        *(undefined4 *)(pdVar2 + local_11c) = local_188;
        uStack_184 = (undefined4)((ulonglong)dVar9 >> 0x20);
        *(undefined4 *)((int)pdVar2 + local_11c * 8 + 4) = uStack_184;
      }
    }
  }
  FUN_1001013e((int)(pdVar2 + iVar8 + -1),(local_178 - iVar8) + 1);
  if (6000 < (*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1) {
    local_170 = (double)(((*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1) / 3000 + -2) + 4.0;
  }
  local_110 = (double)CONCAT44(*(undefined4 *)((int)pdVar2 + iVar8 * 8 + 4),
                               *(undefined4 *)(pdVar2 + iVar8));
  local_11c = iVar8;
  while (local_11c = local_11c + 1, local_11c <= local_178) {
    local_118 = *(undefined4 *)(pdVar2 + local_11c);
    uStack_114 = *(undefined4 *)((int)pdVar2 + local_11c * 8 + 4);
    local_110 = ((local_170 - _DAT_10038530) * local_110 + (double)CONCAT44(uStack_114,local_118)) /
                local_170;
    if (local_110 < (double)CONCAT44(uStack_114,local_118)) {
      local_158 = local_158 + 1;
      if (local_158 == 1) {
        local_174 = local_174 + 1;
        if (local_174 != 1) {
          fVar10 = (float)(local_11c - local_fc);
          if (local_11c <= local_178) {
            local_15c = fVar10 * fVar10 + local_15c;
            local_124 = local_124 + fVar10;
            local_100 = local_100 + _DAT_10038538;
          }
          ObsInpSpec::widthDataPt(local_120,local_174,fVar10);
        }
        local_fc = local_11c;
      }
    }
    else {
      local_158 = 0;
    }
  }
  free_dvector(pdVar2,1,local_178);
  ObsInpSpec::putativePks(local_120,local_174);
  if ((local_174 != 0) && (_DAT_1003853c != local_100)) {
    iVar8 = ftol();
    fVar10 = local_124 / local_100;
    dVar9 = sqrt((double)(local_15c / local_100 - fVar10 * fVar10));
    fVar11 = (float)dVar9;
    iVar3 = ftol();
    iVar4 = ftol();
    ObsInpSpec::decimateData(local_120,iVar4,iVar3,fVar10,fVar11);
    if ((iVar8 < 2) ||
       (((*(int *)(this + 0xc0) != 2 && (*(int *)(this + 0xc0) != 4)) &&
        (*(int *)(this + 0xc0) != 6)))) {
      ObsInpSpec::rateChgAction(local_120,0,0);
    }
    else {
      iVar3 = *(int *)(this + 0xbc);
      iVar4 = *(int *)(this + 0xbc);
      iVar1 = *(int *)(this + 0xb8);
      ObsInpSpec::rateChgAction(local_120,1,iVar8);
      if (((iVar4 - iVar1) + 1) / iVar8 < 0x898) {
        *(int *)(this + 0xbc) = *(int *)(this + 0xb8) + iVar8 * 0x898;
        iVar4 = rows(this);
        if (iVar4 < *(int *)(this + 0xbc)) {
          iVar4 = rows(this);
          *(int *)(this + 0xbc) = iVar4;
        }
      }
      iVar3 = iVar3 / iVar8;
      ppdVar5 = dmatrix(1,iVar3,1,4);
      pfVar6 = vector(1,iVar3);
      local_1ac = 1;
      local_1b0 = 1;
      for (local_1a4 = 1; local_1a4 <= iVar3; local_1a4 = local_1a4 + 1) {
        for (local_17c = 1; local_17c < 5; local_17c = local_17c + 1) {
          local_1c4 = 0;
          local_1cc = 0.0;
          for (local_1c8 = 0; local_1c8 < iVar8; local_1c8 = local_1c8 + 1) {
            iVar4 = ftol();
            local_1c4 = local_1c4 + iVar4;
            local_1cc = local_1cc + *(float *)(*(int *)(this + 0x300) + (local_1c8 + local_1b0) * 4)
            ;
          }
          ppdVar5[local_1ac][local_17c] = (double)(local_1c4 / iVar8);
          pfVar6[local_1ac] = local_1cc / (float)iVar8;
        }
        local_1b0 = local_1b0 + iVar8;
        local_1ac = local_1ac + 1;
      }
      pm(this,ppdVar5,pfVar6,iVar3,*(int *)(this + 0xb8) / iVar8,*(int *)(this + 0xbc) / iVar8);
      local_104 = 1;
    }
    uVar7 = ftol();
    *(undefined4 *)(this + 0x1b0) = uVar7;
  }
  iVar8 = local_104;
  local_8 = 0xffffffff;
  ObsInpSpec::~ObsInpSpec(local_f8);
  ExceptionList = local_10;
  return iVar8;
}

//===== 0x1001013e =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_1001013e(int param_1,int param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined8 local_10;
  undefined4 local_8;
  
  local_10 = *(double *)(param_1 + 8);
  for (local_8 = 2; local_8 <= param_2 + -1; local_8 = local_8 + 1) {
    uVar1 = *(undefined4 *)(param_1 + -8 + local_8 * 8);
    uVar2 = *(undefined4 *)(param_1 + -4 + local_8 * 8);
    *(undefined4 *)(param_1 + -8 + local_8 * 8) = (undefined4)local_10;
    *(undefined4 *)(param_1 + -4 + local_8 * 8) = local_10._4_4_;
    local_10 = (double)CONCAT44(*(undefined4 *)(param_1 + 0xc + local_8 * 8),
                                *(undefined4 *)(param_1 + 8 + local_8 * 8)) / _DAT_10038560 +
               (double)CONCAT44(*(undefined4 *)(param_1 + 4 + local_8 * 8),
                                *(undefined4 *)(param_1 + local_8 * 8)) / _DAT_10038568 +
               (double)CONCAT44(uVar2,uVar1) / _DAT_10038560;
  }
  *(undefined4 *)(param_1 + -8 + local_8 * 8) = (undefined4)local_10;
  *(undefined4 *)(param_1 + -4 + local_8 * 8) = local_10._4_4_;
  return;
}

//===== 0x100101fe =====

void FUN_100101fe(void)

{
  FUN_10010208();
  return;
}

//===== 0x10010208 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10010208(void)

{
  _DAT_10041d68 = acos(-1.0);
  return;
}

//===== 0x10010230 =====

/* public: int __thiscall LMConvert::nout(void)const  */

int __thiscall LMConvert::nout(LMConvert *this)

{
                    /* 0x10230  285  ?nout@LMConvert@@QBEHXZ */
  return *(int *)(this + 0x14);
}

//===== 0x10010250 =====

/* public: float const __thiscall LMConvert::output(int)const  */

float __thiscall LMConvert::output(LMConvert *this,int param_1)

{
                    /* 0x10250  296  ?output@LMConvert@@QBE?BMH@Z */
  return *(float *)(*(int *)(this + 0x18) + param_1 * 4);
}

//===== 0x10010270 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int __cdecl FUN_10010270(int param_1,int param_2,int *param_3)

{
  int iVar1;
  double *pdVar2;
  undefined4 local_84;
  undefined4 local_80;
  int local_74;
  int local_70;
  int local_6c;
  double local_68 [5];
  int local_40;
  int local_3c;
  int local_38;
  int local_34;
  int local_30;
  int local_2c;
  int local_28 [3];
  double **local_1c;
  int local_18;
  int local_14 [4];
  
  local_6c = 0;
  local_28[2] = 0;
  local_28[1] = 0;
  local_28[0] = 0;
  FUN_10010698(&local_6c,param_3,param_2,&local_74);
  if ((local_6c == 0) || (*param_3 == 0)) {
    local_6c = 0;
  }
  else {
    local_1c = dmatrix(1,param_2,1,4);
    for (local_70 = 1; local_70 < 5; local_70 = local_70 + 1) {
      for (local_2c = 1; local_2c <= param_2; local_2c = local_2c + 1) {
        iVar1 = *(int *)(param_1 + local_2c * 4);
        local_84 = *(undefined4 *)(iVar1 + local_70 * 8);
        local_80 = *(undefined4 *)(iVar1 + 4 + local_70 * 8);
        if (_DAT_10038570 <= (double)CONCAT44(local_80,local_84)) {
          local_84 = 0;
          local_80 = 0x40b77000;
        }
        pdVar2 = local_1c[local_2c];
        *(undefined4 *)(pdVar2 + local_70) = local_84;
        *(undefined4 *)((int)pdVar2 + local_70 * 8 + 4) = local_80;
      }
    }
    FUN_100108cb((int)local_1c,param_2,(int)local_68);
    for (local_70 = 1; local_70 < 5; local_70 = local_70 + 1) {
      for (local_2c = 1; local_2c <= param_2; local_2c = local_2c + 1) {
        local_1c[local_2c][local_70] = local_1c[local_2c][local_70] * local_68[local_70];
      }
    }
    local_38 = (int)*(short *)(local_6c + local_74 * 0xc);
    local_40 = (int)*(short *)(local_6c + 2 + local_74 * 0xc);
    FUN_10010b2e((int)local_1c,local_38,local_40,0xf,2,local_28);
    FUN_10010a4e(local_14,local_28,&local_18);
    for (local_34 = 0; local_34 < *param_3; local_34 = local_34 + 1) {
      for (local_30 = 0; local_30 < 4; local_30 = local_30 + 1) {
        *(short *)(local_6c + local_34 * 0xc + 4 + local_30 * 2) = (short)local_14[local_30];
      }
    }
    FUN_10010ca7((int)local_1c,1,param_2,(int)local_14);
    local_34 = local_74;
    while (local_34 = local_34 + -1, -1 < local_34) {
      local_38 = (int)*(short *)(local_6c + local_34 * 0xc);
      local_40 = (int)*(short *)(local_6c + 2 + local_34 * 0xc);
      FUN_10010b2e((int)local_1c,local_38,local_40,3,1,local_28);
      FUN_10010a4e(local_14,local_28,&local_18);
      for (local_3c = 0; local_3c <= local_34; local_3c = local_3c + 1) {
        for (local_30 = 0; local_30 < 4; local_30 = local_30 + 1) {
          *(short *)(local_6c + local_3c * 0xc + 4 + local_30 * 2) =
               *(short *)(local_6c + local_3c * 0xc + 4 + local_30 * 2) + (short)local_14[local_30];
        }
      }
      FUN_10010ca7((int)local_1c,1,local_38 + -1,(int)local_14);
    }
    for (local_34 = local_74; local_34 < *param_3; local_34 = local_34 + 1) {
      local_38 = (int)*(short *)(local_6c + local_34 * 0xc);
      local_40 = (int)*(short *)(local_6c + 2 + local_34 * 0xc);
      FUN_10010b2e((int)local_1c,local_38,local_40,3,1,local_28);
      FUN_10010a4e(local_14,local_28,&local_18);
      for (local_3c = local_34; local_3c < *param_3; local_3c = local_3c + 1) {
        for (local_30 = 0; local_30 < 4; local_30 = local_30 + 1) {
          *(short *)(local_6c + local_3c * 0xc + 4 + local_30 * 2) =
               *(short *)(local_6c + local_3c * 0xc + 4 + local_30 * 2) + (short)local_14[local_30];
        }
      }
      FUN_10010ca7((int)local_1c,local_40 + 1,param_2,(int)local_14);
    }
    free_dmatrix(local_1c,1,param_2,1,4);
  }
  return local_6c;
}

//===== 0x10010698 =====

void __cdecl FUN_10010698(undefined4 *param_1,int *param_2,int param_3,int *param_4)

{
  undefined2 *puVar1;
  int local_10;
  int local_c;
  
  *param_1 = 0;
  *param_2 = 0;
  if (0x95f < param_3) {
    *param_2 = (param_3 + -0x7e9) / 0x2ee + 6;
    *param_4 = (6 < *param_2) + 5;
    puVar1 = operator_new(*param_2 * 0xc);
    *param_1 = puVar1;
    for (local_10 = 0; local_10 < *param_2; local_10 = local_10 + 1) {
      puVar1[local_10 * 6] = 0;
      puVar1[local_10 * 6 + 1] = 0;
      for (local_c = 0; local_c < 4; local_c = local_c + 1) {
        puVar1[local_10 * 6 + local_c + 2] = 0;
      }
    }
    *puVar1 = 1;
    puVar1[1] = 0x96;
    puVar1[6] = puVar1[1] + 1;
    puVar1[7] = puVar1[1] + 0xfa;
    puVar1[0xc] = puVar1[7] + 1;
    puVar1[0xd] = puVar1[7] + 500;
    puVar1[0x12] = puVar1[0xd] + 1;
    puVar1[0x13] = puVar1[0xd] + 500;
    puVar1[0x18] = puVar1[0x13] + 1;
    puVar1[0x19] = puVar1[0x13] + 500;
    puVar1[0x1e] = puVar1[0x19] + 1;
    puVar1[0x1f] = puVar1[0x19] + 500;
    for (local_10 = 6; local_10 < *param_2; local_10 = local_10 + 1) {
      puVar1[local_10 * 6] = puVar1[(local_10 + -1) * 6 + 1] + 1;
      puVar1[local_10 * 6 + 1] = puVar1[(local_10 + -1) * 6 + 1] + 0x2ee;
    }
    if (param_3 < (short)puVar1[(local_10 + -1) * 6 + 1]) {
      puVar1[(local_10 + -1) * 6 + 1] = (undefined2)param_3;
    }
  }
  return;
}

//===== 0x100108cb =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_100108cb(int param_1,int param_2,int param_3)

{
  size_t _NumOfElements;
  void *_Base;
  int iVar1;
  int local_48;
  int local_44;
  double local_40;
  undefined8 uStack_2c;
  double local_24 [4];
  
  _NumOfElements = (param_2 * 2 + 10) / 10;
  local_40 = 0.0;
  _Base = operator_new(_NumOfElements << 3);
  for (local_44 = 1; local_44 < 5; local_44 = local_44 + 1) {
    for (local_48 = 0; local_48 < (int)_NumOfElements; local_48 = local_48 + 1) {
      iVar1 = *(int *)(param_1 + (_NumOfElements * 2 + local_48) * 4);
      *(undefined4 *)((int)_Base + local_48 * 8) = *(undefined4 *)(iVar1 + local_44 * 8);
      *(undefined4 *)((int)_Base + local_48 * 8 + 4) = *(undefined4 *)(iVar1 + 4 + local_44 * 8);
    }
    qsort(_Base,_NumOfElements,8,FUN_10010a00);
    iVar1 = (int)(_NumOfElements * 0x5f) / 100;
    *(undefined4 *)(&uStack_2c + local_44) = *(undefined4 *)((int)_Base + iVar1 * 8);
    *(undefined4 *)((int)local_24 + local_44 * 8 + -4) = *(undefined4 *)((int)_Base + iVar1 * 8 + 4)
    ;
    local_40 = local_40 + (double)(&uStack_2c)[local_44];
  }
  for (local_44 = 1; local_44 < 5; local_44 = local_44 + 1) {
    *(double *)(param_3 + local_44 * 8) =
         (_DAT_10038578 * local_40) / (double)(&uStack_2c)[local_44];
  }
  operator_delete(_Base);
  return;
}

//===== 0x10010a00 =====

undefined4 __cdecl FUN_10010a00(double *param_1,double *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x10010a4e =====

void __cdecl FUN_10010a4e(int *param_1,int *param_2,int *param_3)

{
  int local_c;
  int local_8;
  
  *param_3 = 0;
  param_1[3] = 0;
  local_c = 0;
  param_1[2] = param_2[2];
  if (param_1[2] < 0) {
    local_c = param_1[2];
  }
  param_1[1] = param_1[2] + param_2[1];
  if (param_1[1] < local_c) {
    local_c = param_1[1];
  }
  *param_1 = param_1[1] + *param_2;
  if (*param_1 < local_c) {
    local_c = *param_1;
  }
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    param_1[local_8] = param_1[local_8] - local_c;
    if (*param_3 < param_1[local_8]) {
      *param_3 = param_1[local_8];
    }
  }
  return;
}

//===== 0x10010b2e =====

void __cdecl FUN_10010b2e(int param_1,int param_2,int param_3,int param_4,int param_5,int *param_6)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 local_50;
  undefined4 uStack_4c;
  undefined8 local_48;
  int local_40;
  undefined4 local_3c;
  int aiStack_38 [5];
  int local_24;
  int local_20;
  int local_1c;
  int local_18;
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
  local_3c = 0;
  aiStack_38[0] = 0;
  for (local_1c = -param_4; local_1c <= param_4; local_1c = local_1c + param_5) {
    for (local_20 = -param_4; local_20 <= param_4; local_20 = local_20 + param_5) {
      for (local_24 = -param_4; local_24 <= param_4; local_24 = local_24 + param_5) {
        local_48 = 0.0;
        local_18 = local_1c;
        local_14 = local_20;
        local_10 = local_24;
        FUN_10010a4e(aiStack_38 + 1,&local_18,&local_8);
        for (local_c = param_2; local_c <= param_3 - local_8; local_c = local_c + 1) {
          local_50 = 0;
          uStack_4c = 0;
          for (local_40 = 1; local_40 < 5; local_40 = local_40 + 1) {
            iVar1 = *(int *)(param_1 + ((local_8 - aiStack_38[local_40]) + local_c) * 4);
            uVar2 = *(undefined4 *)(iVar1 + local_40 * 8);
            uVar3 = *(undefined4 *)(iVar1 + 4 + local_40 * 8);
            if ((double)CONCAT44(uStack_4c,local_50) < (double)CONCAT44(uVar3,uVar2)) {
              local_50 = uVar2;
              uStack_4c = uVar3;
            }
          }
          local_48 = local_48 + (double)CONCAT44(uStack_4c,local_50);
        }
        if ((double)CONCAT44(aiStack_38[0],local_3c) < local_48) {
          local_3c = (undefined4)local_48;
          aiStack_38[0] = local_48._4_4_;
          *param_6 = local_18;
          param_6[1] = local_14;
          param_6[2] = local_10;
        }
      }
    }
  }
  return;
}

//===== 0x10010ca7 =====

void __cdecl FUN_10010ca7(int param_1,int param_2,int param_3,int param_4)

{
  int iVar1;
  int iVar2;
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  
  for (local_8 = 1; local_8 < 5; local_8 = local_8 + 1) {
    if (*(int *)(param_4 + -4 + local_8 * 4) != 0) {
      local_10 = param_3;
      for (local_c = param_3 - *(int *)(param_4 + -4 + local_8 * 4); param_2 <= local_c;
          local_c = local_c + -1) {
        iVar1 = *(int *)(param_1 + local_c * 4);
        iVar2 = *(int *)(param_1 + local_10 * 4);
        *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
        *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
        local_10 = local_10 + -1;
      }
      for (; param_2 <= local_10; local_10 = local_10 + -1) {
        iVar1 = *(int *)(param_1 + local_10 * 4);
        *(undefined4 *)(iVar1 + local_8 * 8) = 0;
        *(undefined4 *)(iVar1 + 4 + local_8 * 8) = 0;
      }
    }
  }
  return;
}

//===== 0x10010d6d =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_10010d6d(int param_1,int param_2,int param_3,int param_4)

{
  short sVar1;
  int iVar2;
  int iVar3;
  double dVar4;
  int iVar5;
  short *psVar6;
  int iVar7;
  int local_44;
  int local_40;
  int local_3c;
  int local_38;
  int local_30;
  undefined4 local_28;
  undefined4 uStack_24;
  int local_10;
  int local_c;
  
  for (local_10 = 0; iVar5 = param_4, local_10 < param_4; local_10 = local_10 + 1) {
    iVar5 = param_3 + local_10 * 0xc;
    sVar1 = *(short *)(iVar5 + 4);
    for (local_c = 1; local_c < 4; local_c = local_c + 1) {
      if (*(short *)(iVar5 + 4 + local_c * 2) < sVar1) {
        sVar1 = *(short *)(iVar5 + 4 + local_c * 2);
      }
    }
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      *(short *)(iVar5 + 4 + local_c * 2) = *(short *)(iVar5 + 4 + local_c * 2) - sVar1;
    }
  }
  while (iVar7 = iVar5, local_10 = iVar7 + -1, 0 < local_10) {
    for (local_c = 0; iVar5 = local_10, local_c < 4; local_c = local_c + 1) {
      *(short *)(param_3 + local_10 * 0xc + 4 + local_c * 2) =
           *(short *)(param_3 + local_10 * 0xc + 4 + local_c * 2) -
           *(short *)(param_3 + (iVar7 + -2) * 0xc + 4 + local_c * 2);
    }
  }
  for (local_10 = 1; local_10 < param_4; local_10 = local_10 + 1) {
    iVar5 = param_3 + local_10 * 0xc;
    sVar1 = *(short *)(iVar5 + 4);
    for (local_c = 1; local_c < 4; local_c = local_c + 1) {
      if (*(short *)(iVar5 + 4 + local_c * 2) < sVar1) {
        sVar1 = *(short *)(iVar5 + 4 + local_c * 2);
      }
    }
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      *(short *)(iVar5 + 4 + local_c * 2) = *(short *)(iVar5 + 4 + local_c * 2) - sVar1;
    }
  }
  for (local_10 = 0; local_10 < param_4; local_10 = local_10 + 1) {
    psVar6 = (short *)(param_3 + local_10 * 0xc);
    iVar5 = (int)*psVar6;
    local_28 = 0;
    uStack_24 = 0;
    for (local_38 = 1; local_30 = iVar5, local_38 < 5; local_38 = local_38 + 1) {
      for (; local_30 <= iVar5 + 0x1e; local_30 = local_30 + 1) {
        if ((double)CONCAT44(uStack_24,local_28) <
            *(double *)(*(int *)(param_1 + local_30 * 4) + local_38 * 8)) {
          iVar7 = *(int *)(param_1 + local_30 * 4);
          local_28 = *(undefined4 *)(iVar7 + local_38 * 8);
          uStack_24 = *(undefined4 *)(iVar7 + 4 + local_38 * 8);
        }
      }
    }
    dVar4 = (double)CONCAT44(uStack_24,local_28) / _DAT_10038580;
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      if (psVar6[local_c + 2] != 0) {
        local_3c = param_2 - psVar6[local_c + 2];
        local_40 = param_2;
        iVar7 = local_c + 1;
        local_44 = iVar5;
        if (dVar4 <= *(double *)(*(int *)(param_1 + iVar5 * 4) + iVar7 * 8)) {
          while ((local_44 <= param_2 &&
                 (dVar4 < *(double *)(*(int *)(param_1 + local_44 * 4) + iVar7 * 8)))) {
            local_44 = local_44 + 1;
          }
          while ((local_44 <= param_2 &&
                 (*(double *)(*(int *)(param_1 + local_44 * 4) + iVar7 * 8) <
                  *(double *)(*(int *)(param_1 + -4 + local_44 * 4) + iVar7 * 8)))) {
            local_44 = local_44 + 1;
          }
        }
        for (; local_44 <= local_3c; local_3c = local_3c + -1) {
          iVar2 = *(int *)(param_1 + local_3c * 4);
          iVar3 = *(int *)(param_1 + local_40 * 4);
          *(undefined4 *)(iVar3 + iVar7 * 8) = *(undefined4 *)(iVar2 + iVar7 * 8);
          *(undefined4 *)(iVar3 + 4 + iVar7 * 8) = *(undefined4 *)(iVar2 + 4 + iVar7 * 8);
          local_40 = local_40 + -1;
        }
        for (; local_44 <= local_40; local_40 = local_40 + -1) {
          iVar2 = *(int *)(param_1 + local_40 * 4);
          *(undefined4 *)(iVar2 + iVar7 * 8) = 0;
          *(undefined4 *)(iVar2 + 4 + iVar7 * 8) = 0;
        }
      }
    }
  }
  return;
}

//===== 0x10011150 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __cdecl
FUN_10011150(int param_1,int param_2,int param_3,int param_4,int param_5,uint param_6,int param_7)

{
  double dVar1;
  int iVar2;
  float10 fVar3;
  undefined4 local_1d8;
  undefined4 local_1d4;
  undefined8 local_1b4;
  double local_1ac;
  double local_19c;
  undefined4 local_194;
  undefined4 local_190;
  undefined4 local_18c;
  undefined4 local_188;
  undefined4 local_184;
  undefined4 uStack_180;
  undefined4 local_17c;
  undefined4 local_178;
  undefined4 local_174;
  undefined4 local_170;
  undefined4 local_16c;
  undefined4 uStack_168;
  undefined4 local_164;
  undefined4 local_160;
  undefined8 local_15c;
  undefined8 local_154;
  undefined4 local_14c;
  undefined4 local_148;
  undefined4 local_144;
  undefined4 local_140;
  undefined4 local_13c;
  undefined4 local_138;
  undefined4 local_12c;
  undefined4 uStack_128;
  uint local_110;
  double local_108;
  undefined4 local_100;
  undefined4 uStack_fc;
  undefined8 local_f8;
  undefined8 local_f0;
  undefined8 local_e8;
  undefined8 local_e0;
  undefined4 *local_d8;
  double local_d4;
  undefined8 local_cc;
  undefined8 local_c4;
  double local_bc;
  undefined8 local_b4;
  undefined4 *local_ac;
  undefined8 local_a8;
  undefined8 local_a0;
  undefined8 local_98;
  undefined8 local_90;
  undefined4 local_88;
  undefined4 uStack_84;
  undefined8 local_80;
  undefined4 *local_78;
  undefined4 local_74;
  undefined4 uStack_70;
  undefined4 local_6c;
  undefined4 uStack_68;
  undefined8 local_64;
  undefined8 local_5c;
  undefined8 local_54;
  undefined4 local_4c;
  undefined4 uStack_48;
  double local_44;
  double local_3c;
  uint local_34;
  uint local_30;
  undefined4 *local_2c;
  undefined4 *local_28;
  undefined4 *local_24;
  undefined4 *local_20;
  void *local_1c;
  void *local_18;
  void *local_14;
  undefined4 local_10;
  undefined4 *local_c;
  uint local_8;
  
  local_10 = 1;
  local_14 = malloc(param_6 * 8 + 8);
  local_1c = malloc(param_6 * 4 + 4);
  local_18 = malloc(param_6 * 4 + 4);
  if (((local_1c == (void *)0x0) || (local_18 == (void *)0x0)) || (local_14 == (void *)0x0)) {
    fprintf((FILE *)(_iob_exref + 0x40),s_out_of_memory_in_fgapcheck_c__li_1003f688,0xac);
    if (local_1c != (void *)0x0) {
      free(local_1c);
      local_1c = (void *)0x0;
    }
    if (local_18 != (void *)0x0) {
      free(local_18);
      local_18 = (void *)0x0;
    }
    if (local_14 != (void *)0x0) {
      free(local_14);
    }
    local_10 = 0;
  }
  else {
    local_c = FUN_10012ad0(2,&DAT_10038588,&DAT_100385b0,3);
    local_28 = FUN_10012ad0(2,&DAT_100385f8,&DAT_10038608,2);
    local_2c = FUN_10012ad0(3,&DAT_10038658,&DAT_10038670,1);
    local_20 = FUN_10012ad0(4,&DAT_10038618,&DAT_10038638,0);
    local_24 = FUN_10012ad0(2,&DAT_10038688,&DAT_10038698,3);
    if (((local_c == (undefined4 *)0x0) || (local_28 == (undefined4 *)0x0)) ||
       ((local_2c == (undefined4 *)0x0 ||
        ((local_20 == (undefined4 *)0x0 || (local_24 == (undefined4 *)0x0)))))) {
      if (local_c != (undefined4 *)0x0) {
        FUN_10013a38(local_c);
      }
      if (local_28 != (undefined4 *)0x0) {
        FUN_10013a38(local_28);
      }
      if (local_2c != (undefined4 *)0x0) {
        FUN_10013a38(local_2c);
      }
      if (local_20 != (undefined4 *)0x0) {
        FUN_10013a38(local_20);
      }
      if (local_24 != (undefined4 *)0x0) {
        FUN_10013a38(local_24);
      }
      free(local_1c);
      free(local_18);
      free(local_14);
      local_10 = 0;
    }
    else {
      local_8 = 1;
      while( true ) {
        if (param_6 < local_8) break;
        local_44 = 0.0;
        if (local_8 < 6) {
          local_110 = 1;
        }
        else {
          local_110 = local_8 - 5;
        }
        local_34 = local_110;
        *(undefined4 *)((int)local_18 + local_8 * 4) = 0;
        *(undefined4 *)((int)local_1c + local_8 * 4) = 0;
        for (local_30 = local_110; local_30 < local_8; local_30 = local_30 + 1) {
          local_44 = (double)*(int *)(param_3 + local_30 * 4) + local_44;
          if (*(char *)(param_5 + local_30) == 'C') {
            *(int *)((int)local_18 + local_8 * 4) = *(int *)((int)local_18 + local_8 * 4) + 1;
          }
          else if (*(char *)(param_5 + local_30) == 'G') {
            *(int *)((int)local_1c + local_8 * 4) = *(int *)((int)local_1c + local_8 * 4) + 1;
          }
        }
        local_3c = (double)(*(int *)(param_2 + local_8 * 4) * (local_8 - local_110));
        if ((_DAT_10038728 == local_3c) || (local_44 < local_3c)) {
          local_3c = 1.0;
          local_44 = 1.0;
        }
        dVar1 = local_3c / local_44;
        fVar3 = FUN_1001204b(5,*(int *)((int)local_1c + local_8 * 4),
                             *(int *)((int)local_18 + local_8 * 4),2,2);
        *(double *)((int)local_14 + local_8 * 8) = (double)(fVar3 * (float10)dVar1);
        local_8 = local_8 + 1;
      }
      for (local_8 = 1; local_8 <= param_6; local_8 = local_8 + 1) {
        local_ac = FUN_10012ad0(3,&DAT_100386a8,&DAT_100386c0,0);
        local_d8 = FUN_10012ad0(3,&DAT_100386d8,&DAT_100386f0,0);
        local_78 = FUN_10012ad0(2,&DAT_10038708,&DAT_10038718,0);
        if (((local_ac == (undefined4 *)0x0) || (local_d8 == (undefined4 *)0x0)) ||
           (local_78 == (undefined4 *)0x0)) {
          if (local_ac != (undefined4 *)0x0) {
            FUN_10013a38(local_ac);
          }
          if (local_d8 != (undefined4 *)0x0) {
            FUN_10013a38(local_d8);
          }
          if (local_78 != (undefined4 *)0x0) {
            FUN_10013a38(local_78);
          }
          local_10 = 0;
          break;
        }
        if ((*(int *)(param_1 + local_8 * 4) == 0) || (*(int *)(param_2 + local_8 * 4) == 0)) {
          FUN_10013a38(local_d8);
          FUN_10013a38(local_ac);
          FUN_10013a38(local_78);
          local_10 = 0;
          break;
        }
        local_a0 = (double)*(int *)(param_3 + local_8 * 4) / (double)*(int *)(param_1 + local_8 * 4)
                   - _DAT_10038730;
        local_e8 = (double)*(int *)(param_4 + local_8 * 4) / (double)*(int *)(param_2 + local_8 * 4)
                   - _DAT_10038730;
        if (local_8 == 1) {
          local_f0 = 0.0;
          local_a8 = 0.0;
        }
        else {
          local_a8 = (double)*(int *)(param_3 + -4 + local_8 * 4) /
                     (double)*(int *)(param_1 + local_8 * 4) - _DAT_10038730;
          local_f0 = (double)*(int *)(param_4 + -4 + local_8 * 4) /
                     (double)*(int *)(param_2 + local_8 * 4) - _DAT_10038730;
        }
        fVar3 = (float10)(*(code *)local_28[3])(local_28,local_a0);
        local_b4 = (double)fVar3;
        fVar3 = (float10)(*(code *)local_20[3])(local_20,(undefined4)local_a0,local_a0._4_4_);
        local_c4 = (double)fVar3;
        fVar3 = (float10)(*(code *)local_2c[3])(local_2c,(undefined4)local_a0,local_a0._4_4_);
        local_e0 = (double)fVar3;
        fVar3 = (float10)(*(code *)local_24[3])(local_24,(undefined4)local_a0,local_a0._4_4_);
        local_90 = (double)fVar3;
        fVar3 = (float10)(*(code *)local_28[3])(local_28,(undefined4)local_a8,local_a8._4_4_);
        local_bc = (double)fVar3;
        fVar3 = (float10)(*(code *)local_20[3])(local_20,(undefined4)local_a8,local_a8._4_4_);
        local_cc = (double)fVar3;
        fVar3 = (float10)(*(code *)local_24[3])(local_24,(undefined4)local_a8,local_a8._4_4_);
        local_98 = (double)fVar3;
        fVar3 = (float10)(*(code *)local_c[3])(local_c,(undefined4)local_e8,local_e8._4_4_);
        local_54 = (double)fVar3;
        fVar3 = (float10)(*(code *)local_c[3])(local_c,(undefined4)local_f0,local_f0._4_4_);
        local_5c = (double)fVar3;
        local_74 = *(undefined4 *)((int)local_14 + local_8 * 8);
        uStack_70 = *(undefined4 *)((int)local_14 + local_8 * 8 + 4);
        if (local_c4 <= local_cc) {
          local_12c = (undefined4)local_c4;
          uStack_128 = local_c4._4_4_;
        }
        else {
          local_12c = (undefined4)local_cc;
          uStack_128 = local_cc._4_4_;
        }
        local_f8 = local_5c;
        if ((double)CONCAT44(uStack_128,local_12c) <= local_5c) {
          if (local_c4 <= local_cc) {
            local_13c = (undefined4)local_c4;
            local_138 = local_c4._4_4_;
          }
          else {
            local_13c = (undefined4)local_cc;
            local_138 = local_cc._4_4_;
          }
          local_f8 = (double)CONCAT44(local_138,local_13c);
        }
        local_144 = local_74;
        local_140 = uStack_70;
        if (local_b4 < (double)CONCAT44(uStack_70,local_74)) {
          local_144 = (undefined4)local_b4;
          local_140 = local_b4._4_4_;
        }
        local_4c = local_144;
        uStack_48 = local_140;
        if (local_98 <= local_b4) {
          local_14c = (undefined4)local_98;
          local_148 = local_98._4_4_;
        }
        else {
          local_14c = (undefined4)local_b4;
          local_148 = local_b4._4_4_;
        }
        if (_DAT_10038730 - local_54 <= (double)CONCAT44(local_148,local_14c)) {
          local_154 = _DAT_10038730 - local_54;
        }
        else {
          local_154 = (double)CONCAT44(local_148,local_14c);
        }
        if (_DAT_10038730 - local_5c <= local_154) {
          local_15c = _DAT_10038730 - local_5c;
        }
        else {
          local_15c = local_154;
        }
        local_64._0_4_ = (undefined4)local_15c;
        local_64._4_4_ = local_15c._4_4_;
        if (local_e0 <= local_90) {
          local_164 = (undefined4)local_90;
          local_160 = local_90._4_4_;
        }
        else {
          local_164 = (undefined4)local_e0;
          local_160 = local_e0._4_4_;
        }
        local_6c = local_164;
        uStack_68 = local_160;
        if (local_15c <= (double)CONCAT44(local_160,local_164)) {
          local_16c = local_164;
          uStack_168 = local_160;
        }
        else {
          local_16c = (undefined4)local_15c;
          uStack_168 = local_15c._4_4_;
        }
        if ((double)CONCAT44(local_140,local_144) <= (double)CONCAT44(uStack_168,local_16c)) {
          if (local_15c <= (double)CONCAT44(local_160,local_164)) {
            local_17c = local_164;
            local_178 = local_160;
          }
          else {
            local_17c = (undefined4)local_15c;
            local_178 = local_15c._4_4_;
          }
          local_174 = local_17c;
          local_170 = local_178;
        }
        else {
          local_174 = local_144;
          local_170 = local_140;
        }
        local_100 = local_174;
        uStack_fc = local_170;
        (*(code *)local_ac[7])(local_ac,local_174,local_170);
        if (local_5c <= local_54) {
          local_184 = (undefined4)local_54;
          uStack_180 = local_54._4_4_;
        }
        else {
          local_184 = (undefined4)local_5c;
          uStack_180 = local_5c._4_4_;
        }
        if ((double)CONCAT44(uStack_180,local_184) <= local_b4) {
          if (local_5c <= local_54) {
            local_194 = (undefined4)local_54;
            local_190 = local_54._4_4_;
          }
          else {
            local_194 = (undefined4)local_5c;
            local_190 = local_5c._4_4_;
          }
          local_18c = local_194;
          local_188 = local_190;
        }
        else {
          local_18c = (undefined4)local_b4;
          local_188 = local_b4._4_4_;
        }
        local_4c = local_18c;
        uStack_48 = local_188;
        local_19c = local_98;
        if (_DAT_10038730 - (double)CONCAT44(uStack_70,local_74) <= _DAT_10038730 - local_98) {
          local_19c = (double)CONCAT44(uStack_70,local_74);
        }
        local_19c = _DAT_10038730 - local_19c;
        local_1ac = local_b4;
        if (local_19c <= local_b4) {
          local_1ac = local_98;
          if (_DAT_10038730 - (double)CONCAT44(uStack_70,local_74) <= _DAT_10038730 - local_98) {
            local_1ac = (double)CONCAT44(uStack_70,local_74);
          }
          local_1ac = _DAT_10038730 - local_1ac;
        }
        if (_DAT_10038730 - local_54 <= local_b4) {
          local_1b4 = _DAT_10038730 - local_54;
        }
        else {
          local_1b4 = local_b4;
        }
        local_6c = (undefined4)local_1b4;
        uStack_68 = local_1b4._4_4_;
        dVar1 = local_1b4;
        if (local_1b4 < local_1ac) {
          dVar1 = local_1ac;
        }
        if ((double)CONCAT44(local_188,local_18c) <= dVar1) {
          local_80 = local_1b4;
          if (local_1b4 < local_1ac) {
            local_80 = local_1ac;
          }
        }
        else {
          local_80 = (double)CONCAT44(local_188,local_18c);
        }
        dVar1 = local_80;
        if (((_DAT_10038738 <= local_54) && ((double)CONCAT44(uStack_fc,local_100) < _DAT_10038740))
           && ((local_80 < _DAT_10038740 && (local_8 < param_6)))) {
          iVar2 = *(int *)(param_3 + local_8 * 4) + *(int *)(param_3 + 4 + local_8 * 4);
          local_a0 = (double)(*(int *)(param_3 + local_8 * 4) +
                             ((int)(iVar2 + (iVar2 >> 0x1f & 3U)) >> 2)) /
                     (double)*(int *)(param_1 + local_8 * 4) - _DAT_10038730;
          local_64 = local_1ac;
          fVar3 = (float10)(*(code *)local_28[3])(local_28,local_a0);
          local_b4 = (double)fVar3;
          dVar1 = local_54;
          if (fVar3 < (float10)local_54) {
            dVar1 = local_b4;
          }
          local_1d4 = (undefined4)((ulonglong)dVar1 >> 0x20);
          local_1d8 = SUB84(dVar1,0);
          local_88 = local_1d8;
          uStack_84 = local_1d4;
          local_1ac = local_64;
          if (dVar1 < local_80) {
            dVar1 = local_80;
          }
        }
        local_80 = dVar1;
        local_64 = local_1ac;
        (*(code *)local_d8[7])(local_d8,dVar1);
        (*(code *)local_78[1])(local_78,local_ac,0);
        (*(code *)local_78[1])(local_78,local_d8,0);
        (*(code *)*local_78)(local_78,&local_108);
        fVar3 = (float10)(*(code *)local_78[4])(local_78);
        local_d4 = (double)fVar3;
        *(float *)(*(int *)(param_7 + local_8 * 4) + 4) = (float)local_108;
        *(float *)(*(int *)(param_7 + local_8 * 4) + 8) = (float)fVar3;
        FUN_10013a38(local_d8);
        FUN_10013a38(local_ac);
        FUN_10013a38(local_78);
      }
      FUN_10013a38(local_c);
      FUN_10013a38(local_28);
      FUN_10013a38(local_2c);
      FUN_10013a38(local_24);
      FUN_10013a38(local_20);
      free(local_14);
      free(local_1c);
      free(local_18);
    }
  }
  return local_10;
}

//===== 0x1001204b =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

float10 __cdecl FUN_1001204b(int param_1,int param_2,int param_3,uint param_4,int param_5)

{
  uint uVar1;
  float10 fVar2;
  float10 fVar3;
  undefined8 local_c;
  
  uVar1 = param_1 + 1U >> 1;
  if (param_4 == 0) {
    param_4 = uVar1;
  }
  if (param_5 == 0) {
    param_5 = param_1 - uVar1;
  }
  fVar2 = FUN_100120d3(param_1,param_4,param_5);
  fVar3 = FUN_100120d3(param_1,param_2,param_3);
  local_c = (double)(fVar3 / (float10)(double)fVar2);
  if ((float10)_DAT_10038730 < fVar3 / (float10)(double)fVar2) {
    local_c = 1.0;
  }
  return (float10)local_c * (float10)local_c;
}

//===== 0x100120d3 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

float10 __cdecl FUN_100120d3(int param_1,int param_2,int param_3)

{
  double dVar1;
  
  dVar1 = sqrt((double)(uint)((param_1 - param_2) * (param_1 - param_2) +
                             (param_1 - param_3) * (param_1 - param_3)) /
               ((double)(uint)(param_1 * param_1) * _DAT_10038748));
  return (float10)_DAT_10038730 - (float10)dVar1;
}

//===== 0x10012140 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __cdecl
FUN_10012140(int param_1,undefined4 param_2,int param_3,int param_4,int param_5,undefined4 param_6,
            int param_7,int param_8)

{
  double _Y;
  undefined4 *puVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  undefined4 *puVar4;
  undefined4 *puVar5;
  float10 fVar6;
  double local_e8;
  undefined8 local_6c;
  undefined4 local_60;
  undefined4 local_5c;
  undefined4 local_58;
  undefined4 local_54;
  undefined4 *local_50;
  undefined4 local_4c;
  undefined4 local_48;
  double local_44;
  undefined4 *local_3c;
  undefined4 *local_38;
  undefined4 *local_34;
  undefined4 *local_30;
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  double local_10;
  int local_8;
  
  local_60 = 0;
  local_5c = 0x3ff00000;
  local_58 = 0;
  local_54 = 0;
  local_28 = 0;
  local_24 = 0;
  local_20 = 0;
  local_1c = 0x3ff00000;
  local_6c = 0.0;
  local_2c = 1;
  if (param_7 == 0) {
    local_2c = 0;
  }
  else {
    for (local_8 = 1; local_8 <= param_7; local_8 = local_8 + 1) {
      local_6c = (double)(*(float *)(param_3 + local_8 * 4) + (float)local_6c);
    }
    local_6c = local_6c / (double)param_7;
    if (_DAT_100388d0 < local_6c) {
      local_6c = 0.05000000074505806;
    }
    local_18 = (undefined4)local_6c;
    local_14 = local_6c._4_4_;
    local_4c = (undefined4)local_6c;
    local_48 = local_6c._4_4_;
    local_10 = _DAT_100388d8 * local_6c * _DAT_100388e0;
    local_44 = local_10;
    local_34 = FUN_10012ad0(3,&DAT_10038750,&DAT_10038768,0);
    local_30 = FUN_10012ad0(4,&DAT_10038780,&DAT_100387a0,2);
    local_38 = FUN_10012ad0(3,&DAT_100387c0,&DAT_100387d8,0);
    local_50 = FUN_10012ad0(2,&DAT_100387f0,&DAT_10038800,0);
    local_3c = FUN_10012ad0(2,&local_4c,&local_60,0);
    puVar1 = FUN_10012ad0(2,&local_18,&local_28,1);
    if (((((local_34 == (undefined4 *)0x0) || (local_30 == (undefined4 *)0x0)) ||
         (local_38 == (undefined4 *)0x0)) ||
        ((local_50 == (undefined4 *)0x0 || (local_3c == (undefined4 *)0x0)))) ||
       (puVar1 == (undefined4 *)0x0)) {
      if (local_34 != (undefined4 *)0x0) {
        FUN_10013a38(local_34);
      }
      if (local_30 != (undefined4 *)0x0) {
        FUN_10013a38(local_30);
      }
      if (local_38 != (undefined4 *)0x0) {
        FUN_10013a38(local_38);
      }
      if (local_50 != (undefined4 *)0x0) {
        FUN_10013a38(local_50);
      }
      if (local_3c != (undefined4 *)0x0) {
        FUN_10013a38(local_3c);
      }
      if (puVar1 != (undefined4 *)0x0) {
        FUN_10013a38(puVar1);
      }
      local_2c = 0;
    }
    else {
      for (local_8 = 1; local_8 <= param_7; local_8 = local_8 + 1) {
        _Y = (double)*(int *)(param_1 + local_8 * 4);
        puVar2 = FUN_10012ad0(2,&DAT_100388b0,&DAT_100388c0,0);
        puVar3 = FUN_10012ad0(3,&DAT_10038810,&DAT_10038828,0);
        puVar4 = FUN_10012ad0(4,&DAT_10038840,&DAT_10038860,0);
        puVar5 = FUN_10012ad0(3,&DAT_10038880,&DAT_10038898,0);
        if (((puVar2 == (undefined4 *)0x0) || (puVar3 == (undefined4 *)0x0)) ||
           ((puVar4 == (undefined4 *)0x0 || (puVar5 == (undefined4 *)0x0)))) {
          if (puVar2 != (undefined4 *)0x0) {
            FUN_10013a38(puVar2);
          }
          if (puVar3 != (undefined4 *)0x0) {
            FUN_10013a38(puVar3);
          }
          if (puVar4 != (undefined4 *)0x0) {
            FUN_10013a38(puVar4);
          }
          if (puVar5 != (undefined4 *)0x0) {
            FUN_10013a38(puVar5);
          }
          local_2c = 0;
          break;
        }
        if ((_Y / _DAT_100388e8 <= (double)*(int *)(param_4 + local_8 * 4)) &&
           ((double)*(int *)(param_4 + local_8 * 4) <= _Y)) {
          fmod((double)*(int *)(param_4 + local_8 * 4),_Y);
        }
        if ((_Y / _DAT_100388e8 <= (double)*(int *)(param_5 + local_8 * 4)) &&
           ((double)*(int *)(param_5 + local_8 * 4) <= _Y)) {
          fmod((double)*(int *)(param_5 + local_8 * 4),_Y);
        }
        if (_DAT_100388f0 == _Y) {
          FUN_10013a38(puVar2);
          FUN_10013a38(puVar3);
          FUN_10013a38(puVar4);
          FUN_10013a38(puVar5);
          local_2c = 0;
          break;
        }
        (*(code *)local_34[3])();
        (*(code *)local_34[3])();
        (*(code *)local_30[3])();
        (*(code *)local_30[3])();
        (*(code *)local_38[3])();
        (*(code *)local_50[3])();
        (*(code *)local_3c[3])();
        (*(code *)puVar1[3])();
        (*(code *)puVar3[7])();
        (*(code *)puVar4[7])();
        (*(code *)puVar5[7])();
        (*(code *)puVar2[1])();
        (*(code *)puVar2[1])();
        (*(code *)puVar2[1])();
        (*(code *)*puVar2)(puVar2);
        fVar6 = (float10)(*(code *)puVar2[4])();
        *(float *)(*(int *)(param_8 + local_8 * 4) + 4) = (float)local_e8;
        *(float *)(*(int *)(param_8 + local_8 * 4) + 8) = (float)fVar6;
        if ((_DAT_100388f8 == *(float *)(*(int *)(param_8 + local_8 * 4) + 4)) &&
           (_DAT_100388f8 == *(float *)(*(int *)(param_8 + local_8 * 4) + 8))) {
          *(undefined4 *)(*(int *)(param_8 + local_8 * 4) + 4) = 0x3f800000;
          *(undefined4 *)(*(int *)(param_8 + local_8 * 4) + 8) = 0x3f000000;
        }
        FUN_10013a38(puVar2);
        FUN_10013a38(puVar3);
        FUN_10013a38(puVar4);
        FUN_10013a38(puVar5);
      }
      FUN_10013a38(local_34);
      FUN_10013a38(local_30);
      FUN_10013a38(local_50);
      FUN_10013a38(local_38);
      FUN_10013a38(puVar1);
      FUN_10013a38(local_3c);
    }
  }
  return local_2c;
}

//===== 0x10012ad0 =====

undefined4 * __cdecl FUN_10012ad0(int param_1,void *param_2,void *param_3,undefined4 param_4)

{
  undefined4 *puVar1;
  void *pvVar2;
  
  puVar1 = malloc(0x38);
  if (puVar1 != (undefined4 *)0x0) {
    puVar1[8] = param_1;
    if (param_1 < 1) {
      puVar1[8] = 0;
    }
    else {
      *puVar1 = FUN_10013818;
      puVar1[1] = FUN_10012f4d;
      puVar1[2] = FUN_10012e31;
      puVar1[3] = FUN_10012c6c;
      puVar1[4] = FUN_10012dbd;
      puVar1[5] = FUN_10012ec6;
      puVar1[6] = FUN_10012e44;
      puVar1[7] = FUN_10012f0b;
      puVar1[0xb] = param_4;
      switch(param_4) {
      case 1:
        puVar1[0xc] = FUN_100139a4;
        puVar1[0xd] = FUN_10013999;
        break;
      case 2:
        puVar1[0xc] = FUN_10013999;
        puVar1[0xd] = FUN_100139a4;
        break;
      case 3:
        puVar1[0xc] = FUN_100139b9;
        puVar1[0xd] = FUN_100139f4;
        break;
      default:
        puVar1[0xb] = 0;
      case 0:
        puVar1[0xd] = FUN_10013991;
        puVar1[0xc] = FUN_10013991;
      }
      pvVar2 = malloc(param_1 << 4);
      puVar1[9] = pvVar2;
      if (puVar1[9] == 0) {
        puVar1[8] = 0;
      }
      else {
        puVar1[10] = puVar1[9] + puVar1[8] * 8;
        memcpy((void *)puVar1[9],param_2,param_1 << 3);
        memcpy((void *)puVar1[10],param_3,param_1 << 3);
      }
    }
  }
  return puVar1;
}

//===== 0x10012c6c =====

void __cdecl FUN_10012c6c(int param_1,double param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  int local_28;
  int local_1c;
  undefined8 local_c;
  
  if (*(int *)(param_1 + 0x20) == 0) {
    local_c = 0.0;
  }
  else if (**(double **)(param_1 + 0x24) < param_2) {
    if (param_2 < *(double *)(*(int *)(param_1 + 0x24) + -8 + *(int *)(param_1 + 0x20) * 8)) {
      local_1c = 0;
      iVar3 = *(int *)(param_1 + 0x20) + -1;
      while (local_28 = iVar3, iVar4 = (local_1c + local_28) / 2, iVar4 != local_1c) {
        iVar3 = iVar4;
        if (*(double *)(*(int *)(param_1 + 0x24) + iVar4 * 8) < param_2) {
          iVar3 = local_28;
          local_1c = iVar4;
        }
      }
      uVar1 = *(undefined4 *)(*(int *)(param_1 + 0x28) + -8 + local_28 * 8);
      uVar2 = *(undefined4 *)(*(int *)(param_1 + 0x28) + -4 + local_28 * 8);
      local_c = ((double)CONCAT44(*(undefined4 *)(*(int *)(param_1 + 0x28) + 4 + local_28 * 8),
                                  *(undefined4 *)(*(int *)(param_1 + 0x28) + local_28 * 8)) -
                (double)CONCAT44(uVar2,uVar1)) *
                ((param_2 - *(double *)(*(int *)(param_1 + 0x24) + -8 + local_28 * 8)) /
                (*(double *)(*(int *)(param_1 + 0x24) + local_28 * 8) -
                *(double *)(*(int *)(param_1 + 0x24) + -8 + local_28 * 8))) +
                (double)CONCAT44(uVar2,uVar1);
    }
    else {
      local_c = (double)CONCAT44(*(undefined4 *)
                                  (*(int *)(param_1 + 0x28) + -4 + *(int *)(param_1 + 0x20) * 8),
                                 *(undefined4 *)
                                  (*(int *)(param_1 + 0x28) + -8 + *(int *)(param_1 + 0x20) * 8));
    }
  }
  else {
    local_c = **(double **)(param_1 + 0x28);
  }
  (**(code **)(param_1 + 0x30))((undefined4)local_c,local_c._4_4_);
  return;
}

//===== 0x10012dbd =====

void __cdecl FUN_10012dbd(int param_1)

{
  undefined4 local_10;
  undefined4 uStack_c;
  undefined4 local_8;
  
  local_10 = 0;
  uStack_c = 0;
  for (local_8 = 0; local_8 < *(int *)(param_1 + 0x20); local_8 = local_8 + 1) {
    if ((double)CONCAT44(uStack_c,local_10) < *(double *)(*(int *)(param_1 + 0x28) + local_8 * 8)) {
      local_10 = *(undefined4 *)(*(int *)(param_1 + 0x28) + local_8 * 8);
      uStack_c = *(undefined4 *)(*(int *)(param_1 + 0x28) + 4 + local_8 * 8);
    }
  }
  (**(code **)(param_1 + 0x30))(local_10,uStack_c);
  return;
}

//===== 0x10012e31 =====

bool __cdecl FUN_10012e31(int param_1)

{
  return *(int *)(param_1 + 0x20) == 0;
}

//===== 0x10012e44 =====

void __cdecl FUN_10012e44(int param_1)

{
  int local_8;
  
  printf(s_CFuzzySet___s__x_y_1003f6b0);
  for (local_8 = 0; local_8 < *(int *)(param_1 + 0x20); local_8 = local_8 + 1) {
    (**(code **)(param_1 + 0x30))
              (*(undefined4 *)(*(int *)(param_1 + 0x28) + local_8 * 8),
               *(undefined4 *)(*(int *)(param_1 + 0x28) + 4 + local_8 * 8));
    printf(s__8_3lf__8_3lf_1003f6d0,*(undefined4 *)(*(int *)(param_1 + 0x24) + local_8 * 8),
           *(undefined4 *)(*(int *)(param_1 + 0x24) + 4 + local_8 * 8));
  }
  printf(&DAT_1003f6e4);
  return;
}

//===== 0x10012ec6 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_10012ec6(int param_1)

{
  undefined4 local_8;
  
  for (local_8 = 0; local_8 < *(int *)(param_1 + 0x20); local_8 = local_8 + 1) {
    *(double *)(*(int *)(param_1 + 0x28) + local_8 * 8) =
         _DAT_10038900 - *(double *)(*(int *)(param_1 + 0x28) + local_8 * 8);
  }
  return;
}

//===== 0x10012f0b =====

void __cdecl FUN_10012f0b(int param_1,double param_2)

{
  undefined4 local_8;
  
  for (local_8 = 0; local_8 < *(int *)(param_1 + 0x20); local_8 = local_8 + 1) {
    *(double *)(*(int *)(param_1 + 0x28) + local_8 * 8) =
         *(double *)(*(int *)(param_1 + 0x28) + local_8 * 8) * param_2;
  }
  return;
}

//===== 0x10012f4d =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_10012f4d(int param_1,int param_2,int param_3)

{
  bool bVar1;
  double dVar2;
  void *pvVar3;
  float10 fVar4;
  undefined4 local_b0;
  undefined4 local_ac;
  undefined4 local_a4;
  undefined4 local_a0;
  undefined8 local_98;
  undefined4 local_8c;
  undefined4 local_88;
  double local_84;
  undefined4 local_7c;
  undefined4 local_78;
  int local_74;
  int local_70;
  void *local_6c;
  undefined4 local_68;
  undefined4 uStack_64;
  double local_60;
  int local_58;
  code *local_54;
  undefined4 local_50;
  undefined4 local_4c;
  double local_48;
  code *local_40;
  void *local_3c;
  double local_38;
  double local_30;
  undefined4 local_28;
  undefined4 uStack_24;
  undefined8 local_20;
  undefined4 local_18;
  undefined4 uStack_14;
  undefined4 local_10;
  undefined4 uStack_c;
  int local_8;
  
  local_40 = *(code **)(param_1 + 0x30);
  local_54 = *(code **)(param_2 + 0x30);
  if (*(int *)(param_1 + 0x20) != 0) {
    if (*(int *)(param_2 + 0x20) == 0) {
      if (*(int *)(param_1 + 0x24) != 0) {
        free(*(void **)(param_1 + 0x24));
        *(undefined4 *)(param_1 + 0x24) = 0;
      }
      *(undefined4 *)(param_1 + 0x20) = 0;
    }
    else {
      local_3c = malloc((*(int *)(param_1 + 0x20) + *(int *)(param_2 + 0x20)) * 0x20);
      if (local_3c == (void *)0x0) {
        *(undefined4 *)(param_1 + 0x20) = 0;
        if (*(int *)(param_1 + 0x24) != 0) {
          free(*(void **)(param_1 + 0x24));
          *(undefined4 *)(param_1 + 0x24) = 0;
        }
      }
      else {
        local_6c = (void *)((int)local_3c +
                           (*(int *)(param_1 + 0x20) + *(int *)(param_2 + 0x20)) * 0x10);
        if (**(double **)(param_2 + 0x24) <= **(double **)(param_1 + 0x24)) {
          if (**(double **)(param_1 + 0x24) <= **(double **)(param_2 + 0x24)) {
            local_28 = **(undefined4 **)(param_1 + 0x24);
            uStack_24 = (*(undefined4 **)(param_1 + 0x24))[1];
            local_70 = 1;
            local_58 = 1;
          }
          else {
            local_28 = **(undefined4 **)(param_2 + 0x24);
            uStack_24 = (*(undefined4 **)(param_2 + 0x24))[1];
            local_58 = 0;
            local_70 = 1;
          }
        }
        else {
          local_28 = **(undefined4 **)(param_1 + 0x24);
          uStack_24 = (*(undefined4 **)(param_1 + 0x24))[1];
          local_58 = 1;
          local_70 = 0;
        }
        fVar4 = (float10)(*local_40)(**(undefined4 **)(param_1 + 0x28),
                                     (*(undefined4 **)(param_1 + 0x28))[1]);
        local_60 = (double)fVar4;
        fVar4 = (float10)(*local_54)(**(undefined4 **)(param_2 + 0x28),
                                     (*(undefined4 **)(param_2 + 0x28))[1]);
        local_84 = (double)fVar4;
        local_74 = 0;
        dVar2 = local_84;
        if ((param_3 != 0) != local_84 < local_60) {
          dVar2 = local_60;
        }
        local_a0 = (undefined4)((ulonglong)dVar2 >> 0x20);
        local_a4 = SUB84(dVar2,0);
        FUN_10013688(local_28,uStack_24,local_a4,local_a0,(int)local_3c,(int)local_6c,&local_74);
        if (*(double *)(*(int *)(param_1 + 0x24) + -8 + *(int *)(param_1 + 0x20) * 8) <
            *(double *)(*(int *)(param_2 + 0x24) + -8 + *(int *)(param_2 + 0x20) * 8)) {
          local_50 = *(undefined4 *)(*(int *)(param_2 + 0x24) + -8 + *(int *)(param_2 + 0x20) * 8);
          local_4c = *(undefined4 *)(*(int *)(param_2 + 0x24) + -4 + *(int *)(param_2 + 0x20) * 8);
        }
        else {
          local_50 = *(undefined4 *)(*(int *)(param_1 + 0x24) + -8 + *(int *)(param_1 + 0x20) * 8);
          local_4c = *(undefined4 *)(*(int *)(param_1 + 0x24) + -4 + *(int *)(param_1 + 0x20) * 8);
        }
        if (local_58 < *(int *)(param_1 + 0x20)) {
          local_18 = *(undefined4 *)(*(int *)(param_1 + 0x24) + local_58 * 8);
          uStack_14 = *(undefined4 *)(*(int *)(param_1 + 0x24) + 4 + local_58 * 8);
          fVar4 = (float10)(*local_40)(*(undefined4 *)(*(int *)(param_1 + 0x28) + local_58 * 8),
                                       *(undefined4 *)(*(int *)(param_1 + 0x28) + 4 + local_58 * 8))
          ;
        }
        else {
          local_18 = local_50;
          uStack_14 = local_4c;
          fVar4 = (float10)(*local_40)(*(undefined4 *)(*(int *)(param_1 + 0x28) + -8 + local_58 * 8)
                                       ,*(undefined4 *)
                                         (*(int *)(param_1 + 0x28) + -4 + local_58 * 8));
        }
        local_38 = (double)fVar4;
        if (local_70 < *(int *)(param_2 + 0x20)) {
          local_10 = *(undefined4 *)(*(int *)(param_2 + 0x24) + local_70 * 8);
          uStack_c = *(undefined4 *)(*(int *)(param_2 + 0x24) + 4 + local_70 * 8);
          fVar4 = (float10)(*local_54)(*(undefined4 *)(*(int *)(param_2 + 0x28) + local_70 * 8),
                                       *(undefined4 *)(*(int *)(param_2 + 0x28) + 4 + local_70 * 8))
          ;
          local_30 = (double)fVar4;
        }
        else {
          local_10 = local_50;
          uStack_c = local_4c;
          fVar4 = (float10)(*local_54)(*(undefined4 *)(*(int *)(param_2 + 0x28) + -8 + local_70 * 8)
                                       ,*(undefined4 *)
                                         (*(int *)(param_2 + 0x28) + -4 + local_70 * 8));
          local_30 = (double)fVar4;
        }
        while ((local_58 < *(int *)(param_1 + 0x20) || (local_70 < *(int *)(param_2 + 0x20)))) {
          if ((double)CONCAT44(uStack_c,local_10) <= (double)CONCAT44(uStack_14,local_18)) {
            if ((double)CONCAT44(uStack_14,local_18) <= (double)CONCAT44(uStack_c,local_10)) {
              bVar1 = local_58 < *(int *)(param_1 + 0x20);
            }
            else {
              bVar1 = false;
            }
          }
          else {
            bVar1 = true;
          }
          if (bVar1) {
            local_68 = local_18;
            uStack_64 = uStack_14;
            local_98 = local_38;
            if ((double)CONCAT44(uStack_c,local_10) == (double)CONCAT44(uStack_24,local_28)) {
              local_48 = 0.0;
            }
            else {
              local_48 = ((double)CONCAT44(uStack_14,local_18) -
                         (double)CONCAT44(uStack_24,local_28)) /
                         ((double)CONCAT44(uStack_c,local_10) - (double)CONCAT44(uStack_24,local_28)
                         );
            }
            local_20 = (local_30 - local_84) * local_48 + local_84;
            local_58 = local_58 + 1;
            if (local_58 < *(int *)(param_1 + 0x20)) {
              local_18 = *(undefined4 *)(*(int *)(param_1 + 0x24) + local_58 * 8);
              uStack_14 = *(undefined4 *)(*(int *)(param_1 + 0x24) + 4 + local_58 * 8);
              fVar4 = (float10)(*local_40)(*(undefined4 *)(*(int *)(param_1 + 0x28) + local_58 * 8),
                                           *(undefined4 *)
                                            (*(int *)(param_1 + 0x28) + 4 + local_58 * 8));
              local_38 = (double)fVar4;
            }
            else {
              local_18 = local_50;
              uStack_14 = local_4c;
            }
          }
          else {
            local_68 = local_10;
            uStack_64 = uStack_c;
            local_20 = local_30;
            if ((double)CONCAT44(uStack_14,local_18) == (double)CONCAT44(uStack_24,local_28)) {
              local_48 = 0.0;
            }
            else {
              local_48 = ((double)CONCAT44(uStack_c,local_10) - (double)CONCAT44(uStack_24,local_28)
                         ) / ((double)CONCAT44(uStack_14,local_18) -
                             (double)CONCAT44(uStack_24,local_28));
            }
            local_98 = (local_38 - local_60) * local_48 + local_60;
            local_70 = local_70 + 1;
            if (local_70 < *(int *)(param_2 + 0x20)) {
              local_10 = *(undefined4 *)(*(int *)(param_2 + 0x24) + local_70 * 8);
              uStack_c = *(undefined4 *)(*(int *)(param_2 + 0x24) + 4 + local_70 * 8);
              fVar4 = (float10)(*local_54)(*(undefined4 *)(*(int *)(param_2 + 0x28) + local_70 * 8),
                                           *(undefined4 *)
                                            (*(int *)(param_2 + 0x28) + 4 + local_70 * 8));
              local_30 = (double)fVar4;
            }
            else {
              local_10 = local_50;
              uStack_c = local_4c;
            }
          }
          if (((double)CONCAT44(uStack_24,local_28) < (double)CONCAT44(uStack_64,local_68)) &&
             ((local_98 - local_20) * (local_60 - local_84) < _DAT_10038908)) {
            FUN_100137c3((double)CONCAT44(uStack_24,local_28),local_60,
                         (double)CONCAT44(uStack_64,local_68),local_98,local_84,local_20,
                         (double *)&local_7c,(double *)&local_8c);
            FUN_10013688(local_7c,local_78,local_8c,local_88,(int)local_3c,(int)local_6c,&local_74);
          }
          if ((param_3 != 0) == local_20 < local_98) {
            local_b0 = (undefined4)local_20;
            local_ac = local_20._4_4_;
          }
          else {
            local_b0 = (undefined4)local_98;
            local_ac = local_98._4_4_;
          }
          FUN_10013688(local_68,uStack_64,local_b0,local_ac,(int)local_3c,(int)local_6c,&local_74);
          local_28 = local_68;
          uStack_24 = uStack_64;
          local_60 = local_98;
          local_84 = local_20;
        }
        if (*(int *)(param_1 + 0x24) != 0) {
          free(*(void **)(param_1 + 0x24));
          *(undefined4 *)(param_1 + 0x24) = 0;
        }
        pvVar3 = malloc(local_74 << 4);
        *(void **)(param_1 + 0x24) = pvVar3;
        *(int *)(param_1 + 0x28) = *(int *)(param_1 + 0x24) + local_74 * 8;
        *(int *)(param_1 + 0x20) = local_74;
        memcpy(*(void **)(param_1 + 0x24),local_3c,*(int *)(param_1 + 0x20) << 3);
        for (local_8 = 0; local_8 < local_74; local_8 = local_8 + 1) {
          fVar4 = (float10)(**(code **)(param_1 + 0x34))
                                     (*(undefined4 *)((int)local_6c + local_8 * 8),
                                      *(undefined4 *)((int)local_6c + local_8 * 8 + 4));
          *(double *)(*(int *)(param_1 + 0x28) + local_8 * 8) = (double)fVar4;
        }
        if (local_3c != (void *)0x0) {
          free(local_3c);
        }
      }
    }
  }
  return;
}

//===== 0x10013688 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl
FUN_10013688(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,int param_5
            ,int param_6,int *param_7)

{
  int iVar1;
  double dVar2;
  
  if (((*param_7 < 1) ||
      (dVar2 = fabs((double)CONCAT44(param_2,param_1) - *(double *)(param_5 + -8 + *param_7 * 8)),
      _DAT_10038910 <= dVar2)) ||
     (dVar2 = fabs((double)CONCAT44(param_4,param_3) - *(double *)(param_6 + -8 + *param_7 * 8)),
     _DAT_10038918 <= dVar2)) {
    if (1 < *param_7) {
      iVar1 = *param_7 + -2;
      dVar2 = fabs(((double)CONCAT44(param_2,param_1) * *(double *)(param_6 + iVar1 * 8) +
                   (*(double *)(param_5 + iVar1 * 8) - (double)CONCAT44(param_2,param_1)) *
                   *(double *)(param_6 + (*param_7 + -1) * 8) +
                   ((double)CONCAT44(param_4,param_3) - *(double *)(param_6 + iVar1 * 8)) *
                   *(double *)(param_5 + (*param_7 + -1) * 8)) -
                   (double)CONCAT44(param_4,param_3) * *(double *)(param_5 + iVar1 * 8));
      if (dVar2 < _DAT_10038920) {
        *param_7 = *param_7 + -1;
      }
    }
    iVar1 = *param_7;
    *(undefined4 *)(param_5 + iVar1 * 8) = param_1;
    *(undefined4 *)(param_5 + 4 + iVar1 * 8) = param_2;
    iVar1 = *param_7;
    *(undefined4 *)(param_6 + iVar1 * 8) = param_3;
    *(undefined4 *)(param_6 + 4 + iVar1 * 8) = param_4;
    *param_7 = *param_7 + 1;
  }
  return;
}

//===== 0x100137c3 =====

void __cdecl
FUN_100137c3(double param_1,double param_2,double param_3,double param_4,double param_5,
            double param_6,double *param_7,double *param_8)

{
  double dVar1;
  
  dVar1 = ((param_2 - param_4) - param_5) + param_6;
  *param_7 = (param_1 * param_6 + ((param_3 * param_2 - param_1 * param_4) - param_3 * param_5)) /
             dVar1;
  *param_8 = (param_2 * param_6 - param_4 * param_5) / dVar1;
  return;
}

//===== 0x10013818 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __cdecl FUN_10013818(int param_1,double *param_2)

{
  float10 fVar1;
  float10 fVar2;
  double dVar3;
  undefined8 local_1c;
  undefined8 local_14;
  undefined4 local_c;
  undefined4 local_8;
  
  local_8 = 0;
  *(undefined4 *)param_2 = 0;
  *(undefined4 *)((int)param_2 + 4) = 0;
  if (1 < *(int *)(param_1 + 0x20)) {
    local_14 = 0.0;
    local_1c = 0.0;
    for (local_c = 1; local_c < *(int *)(param_1 + 0x20); local_c = local_c + 1) {
      fVar1 = (float10)(**(code **)(param_1 + 0x30))
                                 (*(undefined4 *)(*(int *)(param_1 + 0x28) + local_c * 8),
                                  *(undefined4 *)(*(int *)(param_1 + 0x28) + 4 + local_c * 8));
      fVar2 = (float10)(**(code **)(param_1 + 0x30))
                                 (*(undefined4 *)(*(int *)(param_1 + 0x28) + -8 + local_c * 8),
                                  *(undefined4 *)(*(int *)(param_1 + 0x28) + -4 + local_c * 8));
      local_14 = (*(double *)(*(int *)(param_1 + 0x24) + local_c * 8) -
                 *(double *)(*(int *)(param_1 + 0x24) + -8 + local_c * 8)) *
                 ((_DAT_10038928 * *(double *)(*(int *)(param_1 + 0x24) + local_c * 8) +
                  *(double *)(*(int *)(param_1 + 0x24) + -8 + local_c * 8)) * (double)fVar1 +
                 (_DAT_10038928 * *(double *)(*(int *)(param_1 + 0x24) + -8 + local_c * 8) +
                 *(double *)(*(int *)(param_1 + 0x24) + local_c * 8)) * (double)fVar2) + local_14;
      local_1c = ((double)fVar2 + (double)fVar1) *
                 (*(double *)(*(int *)(param_1 + 0x24) + local_c * 8) -
                 *(double *)(*(int *)(param_1 + 0x24) + -8 + local_c * 8)) + local_1c;
    }
    dVar3 = fabs(local_1c);
    if (_DAT_10038910 < dVar3) {
      *param_2 = local_14 / (_DAT_10038930 * local_1c);
      local_8 = 1;
    }
  }
  return local_8;
}

//===== 0x10013991 =====

float10 __cdecl FUN_10013991(double param_1)

{
  return (float10)param_1;
}

//===== 0x10013999 =====

float10 __cdecl FUN_10013999(double param_1)

{
  return (float10)param_1 * (float10)param_1;
}

//===== 0x100139a4 =====

float10 __cdecl FUN_100139a4(undefined4 param_1,undefined4 param_2)

{
  double dVar1;
  
  dVar1 = sqrt((double)CONCAT44(param_2,param_1));
  return (float10)dVar1;
}

//===== 0x100139b9 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

float10 __cdecl FUN_100139b9(undefined4 param_1,undefined4 param_2)

{
  undefined8 local_c;
  
  if ((double)CONCAT44(param_2,param_1) < _DAT_10038938) {
    local_c = (double)CONCAT44(param_2,param_1) * (double)CONCAT44(param_2,param_1);
  }
  else {
    local_c = sqrt((double)CONCAT44(param_2,param_1));
  }
  return (float10)local_c;
}

//===== 0x100139f4 =====

float10 __cdecl FUN_100139f4(undefined4 param_1,undefined4 param_2)

{
  double dVar1;
  undefined8 local_c;
  
  dVar1 = sqrt(0.5);
  if ((double)CONCAT44(param_2,param_1) < dVar1) {
    local_c = sqrt((double)CONCAT44(param_2,param_1));
  }
  else {
    local_c = (double)CONCAT44(param_2,param_1) * (double)CONCAT44(param_2,param_1);
  }
  return (float10)local_c;
}

//===== 0x10013a38 =====

void __cdecl FUN_10013a38(void *param_1)

{
  if (param_1 != (void *)0x0) {
    if (*(int *)((int)param_1 + 0x24) != 0) {
      free(*(void **)((int)param_1 + 0x24));
      *(undefined4 *)((int)param_1 + 0x24) = 0;
    }
    free(param_1);
  }
  return;
}

//===== 0x10013a80 =====

undefined4 * __thiscall FUN_10013a80(void *this,Wvfm *param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  float *pfVar4;
  double *pdVar5;
  void *pvVar6;
  undefined4 local_8;
  
  *(undefined4 *)this = 0;
  *(Wvfm **)((int)this + 4) = param_1;
  iVar1 = Wvfm::bgni(param_1);
  *(int *)((int)this + 8) = iVar1;
  iVar1 = Wvfm::endi(param_1);
  *(int *)((int)this + 0xc) = iVar1;
  *(undefined4 *)((int)this + 0x14) = param_2;
  *(undefined4 *)((int)this + 0x18) = 0;
  *(undefined4 *)((int)this + 0x1c) = 0;
  *(undefined4 *)((int)this + 0x20) = 0;
  iVar1 = Wvfm::endi(param_1);
  *(int *)((int)this + 0x28) = iVar1;
  iVar1 = Wvfm::endi(param_1);
  iVar2 = Wvfm::bgni(param_1);
  *(int *)((int)this + 0x2c) = (iVar1 - iVar2) * 2 + 2;
  *(undefined4 *)((int)this + 0x30) = 0;
  *(undefined4 *)((int)this + 0x34) = 100;
  *(undefined4 *)((int)this + 0x38) = 0;
  piVar3 = ivector(1,*(long *)((int)this + 0x2c));
  *(int **)((int)this + 0x20) = piVar3;
  if (*(int *)((int)this + 0x20) == 0) {
    *(undefined4 *)this = 1;
  }
  else {
    pfVar4 = vector(1,*(long *)((int)this + 0x2c));
    *(float **)((int)this + 0x1c) = pfVar4;
    if (*(int *)((int)this + 0x1c) == 0) {
      *(undefined4 *)this = 1;
      free_ivector(*(int **)((int)this + 0x20),1,*(long *)((int)this + 0x2c));
    }
    else {
      pdVar5 = dvector(1,*(long *)((int)this + 0x28));
      *(double **)((int)this + 0x18) = pdVar5;
      if (*(int *)((int)this + 0x18) == 0) {
        free_ivector(*(int **)((int)this + 0x20),1,*(long *)((int)this + 0x2c));
        free_vector(*(float **)((int)this + 0x1c),1,*(long *)((int)this + 0x2c));
        *(undefined4 *)this = 1;
      }
      else {
        pvVar6 = operator_new(*(int *)((int)this + 0x34) * 4 + 4);
        *(void **)((int)this + 0x24) = pvVar6;
        if (*(int *)((int)this + 0x24) == 0) {
          free_ivector(*(int **)((int)this + 0x20),1,*(long *)((int)this + 0x2c));
          free_vector(*(float **)((int)this + 0x1c),1,*(long *)((int)this + 0x2c));
          free_dvector(*(double **)((int)this + 0x18),1,*(long *)((int)this + 0x28));
          *(undefined4 *)this = 1;
        }
        else {
          for (local_8 = 0; local_8 <= *(int *)((int)this + 0x34); local_8 = local_8 + 1) {
            *(undefined4 *)(*(int *)((int)this + 0x24) + local_8 * 4) = 0;
          }
          FUN_10013fdc((int)this);
          FUN_1001408d((int)this);
          FUN_1001454c((int)this);
          FUN_100145ea((int)this);
          FUN_1001481b((int)this);
          *(undefined4 *)this = 2;
        }
      }
    }
  }
  return this;
}

//===== 0x10013cdd =====

void __fastcall FUN_10013cdd(int param_1)

{
  FUN_10013cf0(param_1);
  return;
}

//===== 0x10013cf0 =====

void __fastcall FUN_10013cf0(int param_1)

{
  if (*(int *)(param_1 + 0x18) != 0) {
    free_dvector(*(double **)(param_1 + 0x18),1,*(long *)(param_1 + 0x28));
    *(undefined4 *)(param_1 + 0x18) = 0;
  }
  if (*(int *)(param_1 + 0x20) != 0) {
    free_ivector(*(int **)(param_1 + 0x20),1,*(long *)(param_1 + 0x2c));
    *(undefined4 *)(param_1 + 0x20) = 0;
  }
  if (*(int *)(param_1 + 0x1c) != 0) {
    free_vector(*(float **)(param_1 + 0x1c),1,*(long *)(param_1 + 0x2c));
    *(undefined4 *)(param_1 + 0x1c) = 0;
  }
  if (*(int *)(param_1 + 0x24) != 0) {
    operator_delete(*(void **)(param_1 + 0x24));
    *(undefined4 *)(param_1 + 0x24) = 0;
  }
  return;
}

//===== 0x10013da6 =====

undefined4 * __thiscall FUN_10013da6(void *this,undefined4 *param_1)

{
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = param_1[1];
  *(undefined4 *)((int)this + 0x18) = 0;
  *(undefined4 *)((int)this + 0x1c) = 0;
  *(undefined4 *)((int)this + 0x20) = 0;
  FUN_10013df5(this,param_1);
  return this;
}

//===== 0x10013df5 =====

undefined4 * __thiscall FUN_10013df5(void *this,undefined4 *param_1)

{
  int iVar1;
  int iVar2;
  double *pdVar3;
  int *piVar4;
  float *pfVar5;
  void *pvVar6;
  int local_c;
  int local_8;
  
  if (param_1 != this) {
    FUN_10013cf0((int)this);
    *(undefined4 *)this = *param_1;
    Wvfm::operator=(*(Wvfm **)((int)this + 4),(Wvfm *)param_1[1]);
    *(undefined4 *)((int)this + 8) = param_1[2];
    *(undefined4 *)((int)this + 0xc) = param_1[3];
    *(undefined4 *)((int)this + 0x28) = param_1[10];
    *(undefined4 *)((int)this + 0x2c) = param_1[0xb];
    *(undefined4 *)((int)this + 0x30) = param_1[0xc];
    *(undefined4 *)((int)this + 0x34) = param_1[0xd];
    *(undefined4 *)((int)this + 0x38) = param_1[0xe];
    *(undefined4 *)((int)this + 0x14) = param_1[5];
    if (0 < *(int *)((int)this + 0x28)) {
      pdVar3 = dvector(1,*(long *)((int)this + 0x28));
      *(double **)((int)this + 0x18) = pdVar3;
      for (local_c = 1; local_c <= *(int *)((int)this + 0x28); local_c = local_c + 1) {
        iVar1 = param_1[6];
        iVar2 = *(int *)((int)this + 0x18);
        *(undefined4 *)(iVar2 + local_c * 8) = *(undefined4 *)(iVar1 + local_c * 8);
        *(undefined4 *)(iVar2 + 4 + local_c * 8) = *(undefined4 *)(iVar1 + 4 + local_c * 8);
      }
    }
    if (0 < *(int *)((int)this + 0x2c)) {
      piVar4 = ivector(1,*(long *)((int)this + 0x2c));
      *(int **)((int)this + 0x20) = piVar4;
      pfVar5 = vector(1,*(long *)((int)this + 0x2c));
      *(float **)((int)this + 0x1c) = pfVar5;
      for (local_c = 1; local_c <= *(int *)((int)this + 0x30); local_c = local_c + 1) {
        *(undefined4 *)(*(int *)((int)this + 0x20) + local_c * 4) =
             *(undefined4 *)(param_1[8] + local_c * 4);
        *(undefined4 *)(*(int *)((int)this + 0x1c) + local_c * 4) =
             *(undefined4 *)(param_1[7] + local_c * 4);
      }
    }
    if (0 < *(int *)((int)this + 0x34)) {
      pvVar6 = operator_new(*(int *)((int)this + 0x34) * 4 + 4);
      *(void **)((int)this + 0x24) = pvVar6;
      for (local_8 = 0; local_8 <= *(int *)((int)this + 0x34); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)((int)this + 0x24) + local_8 * 4) =
             *(undefined4 *)(param_1[9] + local_8 * 4);
      }
    }
  }
  return this;
}

//===== 0x10013fdc =====

void __fastcall FUN_10013fdc(int param_1)

{
  double dVar1;
  undefined4 local_c;
  undefined4 local_8;
  
  for (local_8 = *(int *)(param_1 + 8); local_8 <= *(int *)(param_1 + 0xc); local_8 = local_8 + 1) {
    dVar1 = Wvfm::sc_la(*(Wvfm **)(param_1 + 4),local_8,1);
    *(double *)(*(int *)(param_1 + 0x18) + local_8 * 8) = dVar1;
    for (local_c = 2; local_c < 5; local_c = local_c + 1) {
      dVar1 = Wvfm::sc_la(*(Wvfm **)(param_1 + 4),local_8,local_c);
      if (*(double *)(*(int *)(param_1 + 0x18) + local_8 * 8) < dVar1) {
        dVar1 = Wvfm::sc_la(*(Wvfm **)(param_1 + 4),local_8,local_c);
        *(double *)(*(int *)(param_1 + 0x18) + local_8 * 8) = dVar1;
      }
    }
  }
  return;
}

//===== 0x1001408d =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_1001408d(int param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  undefined4 uVar6;
  int iVar7;
  undefined8 local_10;
  undefined4 local_8;
  
  local_10 = (double)CONCAT44(*(undefined4 *)
                               (*(int *)(param_1 + 0x18) + 4 + *(int *)(param_1 + 8) * 8),
                              *(undefined4 *)(*(int *)(param_1 + 0x18) + *(int *)(param_1 + 8) * 8))
  ;
  local_8 = *(int *)(param_1 + 8);
  while (local_8 = local_8 + 1, local_8 <= *(int *)(param_1 + 0xc) + -1) {
    uVar1 = *(undefined4 *)(*(int *)(param_1 + 0x18) + -8 + local_8 * 8);
    uVar2 = *(undefined4 *)(*(int *)(param_1 + 0x18) + -4 + local_8 * 8);
    uVar3 = *(undefined4 *)(*(int *)(param_1 + 0x18) + local_8 * 8);
    uVar4 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 4 + local_8 * 8);
    uVar5 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 8 + local_8 * 8);
    uVar6 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 0xc + local_8 * 8);
    iVar7 = *(int *)(param_1 + 0x18);
    *(undefined4 *)(iVar7 + -8 + local_8 * 8) = (undefined4)local_10;
    *(undefined4 *)(iVar7 + -4 + local_8 * 8) = local_10._4_4_;
    local_10 = (double)CONCAT44(uVar6,uVar5) / _DAT_10038940 +
               (double)CONCAT44(uVar4,uVar3) / _DAT_10038948 +
               (double)CONCAT44(uVar2,uVar1) / _DAT_10038940;
  }
  iVar7 = *(int *)(param_1 + 0x18);
  *(undefined4 *)(iVar7 + -8 + local_8 * 8) = (undefined4)local_10;
  *(undefined4 *)(iVar7 + -4 + local_8 * 8) = local_10._4_4_;
  return;
}

//===== 0x10014175 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_10014175(int param_1)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  double dVar4;
  float local_78;
  int local_5c;
  int local_4c;
  int local_40;
  double local_3c;
  double local_2c;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  int local_14;
  int local_10;
  int local_c;
  float local_8;
  
  local_3c = 0.0;
  local_2c = 0.0;
  local_c = 2;
LAB_100141bb:
  if (*(int *)(param_1 + 0x30) <= local_c) {
    local_3c = local_3c / (double)(*(int *)(param_1 + 0x30) + -2);
    dVar4 = sqrt(local_2c / (double)(*(int *)(param_1 + 0x30) + -2) - local_3c * local_3c);
    local_8 = (float)((float10)local_3c + (float10)dVar4);
    if (_DAT_10038950 < local_8) {
      local_8 = 1.0;
    }
    if ((double)local_8 < local_3c - dVar4) {
      local_8 = (float)((float10)local_3c - (float10)dVar4);
    }
    *(undefined4 *)(param_1 + 0x10) = 0;
    for (local_c = 2; local_c < *(int *)(param_1 + 0x30); local_c = local_c + 1) {
      if (*(float *)(*(int *)(param_1 + 0x1c) + local_c * 4) <= local_8) {
        *(int *)(param_1 + 0x10) = *(int *)(param_1 + 0x10) + 1;
      }
    }
    return;
  }
  local_40 = *(int *)(*(int *)(param_1 + 0x20) + -4 + local_c * 4) + 1;
  if (local_c < 3) {
    local_24 = *(undefined4 *)(*(int *)(param_1 + 0x18) + local_40 * 8);
    uStack_20 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 4 + local_40 * 8);
    local_14 = local_40;
    for (; local_40 < *(int *)(*(int *)(param_1 + 0x20) + local_c * 4); local_40 = local_40 + 1) {
      if (*(double *)(*(int *)(param_1 + 0x18) + local_40 * 8) <
          (double)CONCAT44(uStack_20,local_24)) {
        local_14 = local_40;
        local_24 = *(undefined4 *)(*(int *)(param_1 + 0x18) + local_40 * 8);
        uStack_20 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 4 + local_40 * 8);
      }
    }
  }
  else {
    local_24 = local_1c;
    uStack_20 = uStack_18;
    local_14 = local_10;
  }
  local_40 = *(int *)(*(int *)(param_1 + 0x20) + local_c * 4) + 1;
  local_1c = *(undefined4 *)(*(int *)(param_1 + 0x18) + local_40 * 8);
  uStack_18 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 4 + local_40 * 8);
  local_10 = local_40;
  for (; local_40 < *(int *)(*(int *)(param_1 + 0x20) + 4 + local_c * 4); local_40 = local_40 + 1) {
    if (*(double *)(*(int *)(param_1 + 0x18) + local_40 * 8) < (double)CONCAT44(uStack_18,local_1c))
    {
      local_10 = local_40;
      local_1c = *(undefined4 *)(*(int *)(param_1 + 0x18) + local_40 * 8);
      uStack_18 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 4 + local_40 * 8);
    }
  }
  iVar1 = *(int *)(*(int *)(param_1 + 0x20) + local_c * 4);
  uVar2 = *(undefined4 *)(*(int *)(param_1 + 0x18) + iVar1 * 8);
  uVar3 = *(undefined4 *)(*(int *)(param_1 + 0x18) + 4 + iVar1 * 8);
  local_4c = local_10;
  for (local_5c = local_14; local_5c < *(int *)(*(int *)(param_1 + 0x20) + local_c * 4);
      local_5c = local_5c + 1) {
    if (((double)CONCAT44(uVar3,uVar2) - (double)CONCAT44(uStack_20,local_24)) / _DAT_10038948 <=
        *(double *)(*(int *)(param_1 + 0x18) + local_5c * 8)) {
      local_5c = local_5c + -1;
      break;
    }
  }
  do {
    if (local_4c <= *(int *)(*(int *)(param_1 + 0x20) + local_c * 4)) break;
    if (((double)CONCAT44(uVar3,uVar2) - (double)CONCAT44(uStack_18,local_1c)) / _DAT_10038948 <=
        *(double *)(*(int *)(param_1 + 0x18) + local_4c * 8)) {
      local_4c = local_4c + 1;
      break;
    }
    local_4c = local_4c + -1;
  } while( true );
  local_78 = (float)(local_4c - local_5c) /
             ((float)(*(int *)(*(int *)(param_1 + 0x20) + 4 + local_c * 4) -
                     *(int *)(*(int *)(param_1 + 0x20) + -4 + local_c * 4)) / (float)_DAT_10038948);
  if (local_c != 2) {
    local_78 = ((11.0 - _DAT_10038950) * *(float *)(*(int *)(param_1 + 0x1c) + -4 + local_c * 4) +
               local_78) / 11.0;
  }
  *(float *)(*(int *)(param_1 + 0x1c) + local_c * 4) = local_78;
  local_3c = (double)(*(float *)(*(int *)(param_1 + 0x1c) + local_c * 4) + (float)local_3c);
  local_2c = (double)(*(float *)(*(int *)(param_1 + 0x1c) + local_c * 4) *
                      *(float *)(*(int *)(param_1 + 0x1c) + local_c * 4) + (float)local_2c);
  local_c = local_c + 1;
  goto LAB_100141bb;
}

//===== 0x10014528 =====

void FUN_10014528(void)

{
  FUN_10014532();
  return;
}

//===== 0x10014532 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10014532(void)

{
  _DAT_10041dd0 = acos(-1.0);
  return;
}

//===== 0x1001454c =====

void __fastcall FUN_1001454c(int param_1)

{
  int local_8;
  
  *(undefined4 *)(param_1 + 0x30) = 0;
  local_8 = *(int *)(param_1 + 8);
  while (local_8 = local_8 + 1, local_8 < *(int *)(param_1 + 0xc)) {
    if ((*(double *)(*(int *)(param_1 + 0x18) + -8 + local_8 * 8) <
         *(double *)(*(int *)(param_1 + 0x18) + local_8 * 8)) &&
       (*(double *)(*(int *)(param_1 + 0x18) + 8 + local_8 * 8) <
        *(double *)(*(int *)(param_1 + 0x18) + local_8 * 8))) {
      *(int *)(param_1 + 0x30) = *(int *)(param_1 + 0x30) + 1;
      *(int *)(*(int *)(param_1 + 0x20) + *(int *)(param_1 + 0x30) * 4) = local_8;
    }
  }
  return;
}

//===== 0x100145ea =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_100145ea(int param_1)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  int local_2c;
  int local_14;
  int local_c;
  int local_8;
  
  local_14 = 100000;
  local_c = 0;
  for (local_8 = 1; local_8 <= *(int *)(param_1 + 0x30); local_8 = local_8 + 1) {
    iVar1 = *(int *)(*(int *)(param_1 + 0x20) + local_8 * 4);
    for (local_2c = 1; local_2c < 5; local_2c = local_2c + 1) {
      Wvfm::sc_la(*(Wvfm **)(param_1 + 4),iVar1,local_2c);
      iVar2 = ftol();
      if (local_c < iVar2) {
        local_c = iVar2;
      }
      if ((_DAT_10038960 <= (double)iVar2) && (iVar2 < local_14)) {
        local_14 = iVar2;
      }
    }
  }
  for (local_8 = 1; local_8 <= *(int *)(param_1 + 0x30); local_8 = local_8 + 1) {
    iVar1 = *(int *)(*(int *)(param_1 + 0x20) + local_8 * 4);
    for (local_2c = 1; local_2c < 5; local_2c = local_2c + 1) {
      Wvfm::sc_la(*(Wvfm **)(param_1 + 4),iVar1,local_2c);
      ftol();
      iVar2 = ftol();
      *(int *)(*(int *)(param_1 + 0x24) + iVar2 * 4) =
           *(int *)(*(int *)(param_1 + 0x24) + iVar2 * 4) + 1;
    }
  }
  *(undefined4 *)(*(int *)(param_1 + 0x24) + -4 + *(int *)(param_1 + 0x34) * 4) =
       *(undefined4 *)(*(int *)(param_1 + 0x24) + *(int *)(param_1 + 0x34) * 4);
  local_8 = *(int *)(param_1 + 0x34);
  do {
    local_8 = local_8 + -1;
  } while (-1 < local_8);
  ftol();
  uVar3 = ftol();
  *(undefined4 *)(param_1 + 0x38) = uVar3;
  return;
}

//===== 0x1001481b =====

void __fastcall FUN_1001481b(int param_1)

{
  double dVar1;
  int iVar2;
  bool bVar3;
  double dVar4;
  undefined4 local_4c;
  undefined8 local_44;
  undefined4 local_3c;
  undefined4 uStack_38;
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_8;
  
  local_8 = 1;
  do {
    if (*(int *)(param_1 + 0x30) < local_8) {
      return;
    }
    iVar2 = ftol();
    if (*(int *)(param_1 + 0x38) < iVar2) {
      dVar1 = (double)*(int *)(param_1 + 0x38) / (double)iVar2;
      if (local_8 == 1) {
        local_20 = *(int *)(*(int *)(param_1 + 0x20) + 4) * 2 -
                   *(int *)(*(int *)(param_1 + 0x20) + 8);
        if (local_20 < *(int *)(param_1 + 8)) {
          local_20 = *(int *)(param_1 + 8);
        }
      }
      else {
        local_20 = *(int *)(*(int *)(param_1 + 0x20) + -4 + local_8 * 4);
      }
      if (*(int *)(param_1 + 0x30) == local_8) {
        local_28 = *(int *)(*(int *)(param_1 + 0x20) + local_8 * 4) * 2 -
                   *(int *)(*(int *)(param_1 + 0x20) + -4 + local_8 * 4);
        if (*(int *)(param_1 + 0xc) < local_28) {
          local_28 = *(int *)(param_1 + 0xc);
        }
      }
      else {
        local_28 = *(int *)(*(int *)(param_1 + 0x20) + 4 + local_8 * 4);
      }
      local_24 = *(int *)(*(int *)(param_1 + 0x20) + local_8 * 4);
      local_14 = ftol();
      local_24 = local_24 + -1;
      for (local_10 = local_24; local_20 <= local_10; local_10 = local_10 + -1) {
        iVar2 = ftol();
        if (iVar2 < local_14) {
          local_24 = local_10;
          local_14 = ftol();
        }
      }
      local_2c = *(int *)(*(int *)(param_1 + 0x20) + local_8 * 4);
      local_14 = ftol();
      local_2c = local_2c + 1;
      for (local_10 = local_2c; local_10 <= local_28; local_10 = local_10 + 1) {
        iVar2 = ftol();
        if (iVar2 < local_14) {
          local_2c = local_10;
          local_14 = ftol();
        }
      }
      local_3c = 0;
      uStack_38 = 0;
      local_1c = 0;
      if (*(int *)(param_1 + 0x14) == 0) {
        for (local_18 = 1; local_18 < 5; local_18 = local_18 + 1) {
          local_44 = 0.0;
          for (local_10 = local_24; local_10 <= local_2c; local_10 = local_10 + 1) {
            dVar4 = Wvfm::sc_la(*(Wvfm **)(param_1 + 4),local_10,local_18);
            local_44 = dVar4 + local_44;
          }
          if ((double)CONCAT44(uStack_38,local_3c) < local_44) {
            local_3c = (undefined4)local_44;
            uStack_38 = local_44._4_4_;
            local_1c = local_18;
          }
        }
      }
      for (local_10 = local_24; local_10 <= local_2c; local_10 = local_10 + 1) {
        if (*(int *)(param_1 + 0x14) == 0) {
          for (local_18 = 1; local_18 < 5; local_18 = local_18 + 1) {
            bVar3 = local_1c == local_18;
            local_4c = local_24;
            while( true ) {
              if ((bVar3) || (local_2c < local_4c)) goto LAB_10014b37;
              dVar4 = Wvfm::sc_la(*(Wvfm **)(param_1 + 4),local_4c,local_18);
              if ((double)*(int *)(param_1 + 0x38) <= dVar4) break;
              local_4c = local_4c + 1;
            }
            bVar3 = true;
LAB_10014b37:
            if (bVar3) {
              Wvfm::sc_la_mul(*(Wvfm **)(param_1 + 4),local_10,local_18,dVar1);
            }
          }
        }
        else {
          for (local_18 = 1; local_18 < 5; local_18 = local_18 + 1) {
            Wvfm::sc_la_mul(*(Wvfm **)(param_1 + 4),local_10,local_18,dVar1);
          }
        }
      }
    }
    local_8 = local_8 + 1;
  } while( true );
}

//===== 0x10014ba2 =====

void __thiscall FUN_10014ba2(void *this,undefined4 param_1)

{
  printf(s_AttenOutliers_here____p__called_f_1003f734,this,param_1);
  printf(s_m_status____d_1003f760,*(undefined4 *)this);
  printf(s_m_bgn__d_m_end__d_1003f770,*(undefined4 *)((int)this + 8),
         *(undefined4 *)((int)this + 0xc));
  printf(s_m_env1Len__d_m_pk1Len__d_m_npk___1003f784,*(undefined4 *)((int)this + 0x28),
         *(undefined4 *)((int)this + 0x2c),*(undefined4 *)((int)this + 0x30));
  printf(s_m_binLen__d_m_cutOffHt__d_1003f7a8,*(undefined4 *)((int)this + 0x34),
         *(undefined4 *)((int)this + 0x38));
  return;
}

//===== 0x10014c40 =====

/* public: __thiscall LMConvert::LMConvert(float const *,int,int,int) */

LMConvert * __thiscall
LMConvert::LMConvert(LMConvert *this,float *param_1,int param_2,int param_3,int param_4)

{
  float fVar1;
  int iVar2;
  int iVar3;
  void *pvVar4;
  float *pfVar5;
  float *local_28;
  int *local_24;
  int local_1c;
  int local_14;
  float *local_10;
  int local_c;
  
                    /* 0x14c40  10  ??0LMConvert@@QAE@PBMHHH@Z */
  *(int *)this = param_2;
  *(int *)(this + 4) = param_3;
  *(int *)(this + 8) = param_4;
  *(int *)(this + 0xc) = param_3;
  *(int *)(this + 0x10) = param_3 << 1;
  *(int *)(this + 0x14) = (param_2 * param_3) / param_4;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x1c) = 0;
  *(undefined4 *)(this + 0x20) = 0;
  iVar2 = *(int *)(this + 8);
  pvVar4 = operator_new(*(int *)(this + 0xc) << 2);
  *(void **)(this + 0x1c) = pvVar4;
  pvVar4 = operator_new(*(int *)(this + 0x10) << 2);
  *(void **)(this + 0x20) = pvVar4;
  pvVar4 = operator_new(*(int *)(this + 0x14) << 2);
  *(void **)(this + 0x18) = pvVar4;
  local_14 = 0;
  for (local_1c = 0; local_1c < *(int *)(this + 4) * *(int *)(this + 8);
      local_1c = local_1c + *(int *)(this + 8)) {
    iVar3 = *(int *)(this + 4);
    *(int *)(*(int *)(this + 0x1c) + local_14 * 4) = local_1c / *(int *)(this + 4);
    *(float *)(*(int *)(this + 0x20) + local_14 * 8) =
         ((float)*(int *)(this + 4) - (float)(local_1c % iVar3)) / (float)*(int *)(this + 4);
    *(float *)(*(int *)(this + 0x20) + 4 + local_14 * 8) =
         (float)(local_1c % iVar3) / (float)*(int *)(this + 4);
    local_14 = local_14 + 1;
  }
  local_10 = *(float **)(this + 0x18);
  for (local_c = 0; local_c < param_2 / iVar2; local_c = local_c + 1) {
    local_28 = *(float **)(this + 0x20);
    local_24 = *(int **)(this + 0x1c);
    for (local_1c = 0; local_1c < *(int *)(this + 4); local_1c = local_1c + 1) {
      iVar3 = *local_24;
      local_24 = local_24 + 1;
      fVar1 = *local_28;
      pfVar5 = local_28 + 1;
      local_28 = local_28 + 2;
      *local_10 = *pfVar5 * (param_1 + iVar3)[1] + fVar1 * param_1[iVar3];
      local_10 = local_10 + 1;
    }
    param_1 = param_1 + *(int *)(this + 8);
  }
  return this;
}

//===== 0x10014e61 =====

/* public: __thiscall LMConvert::LMConvert(class LMConvert const &) */

LMConvert * __thiscall LMConvert::LMConvert(LMConvert *this,LMConvert *param_1)

{
                    /* 0x14e61  9  ??0LMConvert@@QAE@ABV0@@Z */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x1c) = 0;
  *(undefined4 *)(this + 0x20) = 0;
  operator=(this,param_1);
  return this;
}

//===== 0x10014ed6 =====

/* public: class LMConvert const & __thiscall LMConvert::operator=(class LMConvert const &) */

LMConvert * __thiscall LMConvert::operator=(LMConvert *this,LMConvert *param_1)

{
  void *pvVar1;
  int local_8;
  
                    /* 0x14ed6  47  ??4LMConvert@@QAEABV0@ABV0@@Z */
  if (param_1 != this) {
    release(this);
    *(undefined4 *)this = *(undefined4 *)param_1;
    *(undefined4 *)(this + 4) = *(undefined4 *)(param_1 + 4);
    *(undefined4 *)(this + 8) = *(undefined4 *)(param_1 + 8);
    *(undefined4 *)(this + 0xc) = *(undefined4 *)(param_1 + 0xc);
    *(undefined4 *)(this + 0x10) = *(undefined4 *)(param_1 + 0x10);
    *(undefined4 *)(this + 0x14) = *(undefined4 *)(param_1 + 0x14);
    if (*(int *)(this + 0x14) != 0) {
      pvVar1 = operator_new(*(int *)(this + 0x14) << 2);
      *(void **)(this + 0x18) = pvVar1;
      if (*(int *)(this + 0x18) != 0) {
        for (local_8 = 0; local_8 < *(int *)(this + 0x14); local_8 = local_8 + 1) {
          *(undefined4 *)(*(int *)(this + 0x18) + local_8 * 4) =
               *(undefined4 *)(*(int *)(param_1 + 0x18) + local_8 * 4);
        }
      }
    }
    if (*(int *)(this + 0xc) != 0) {
      pvVar1 = operator_new(*(int *)(this + 0xc) << 2);
      *(void **)(this + 0x1c) = pvVar1;
      if (*(int *)(this + 0x1c) != 0) {
        for (local_8 = 0; local_8 < *(int *)(this + 0xc); local_8 = local_8 + 1) {
          *(undefined4 *)(*(int *)(this + 0x1c) + local_8 * 4) =
               *(undefined4 *)(*(int *)(param_1 + 0x1c) + local_8 * 4);
        }
      }
    }
    if (*(int *)(this + 0x10) != 0) {
      pvVar1 = operator_new(*(int *)(this + 0x10) << 2);
      *(void **)(this + 0x20) = pvVar1;
      if (*(int *)(this + 0x20) != 0) {
        for (local_8 = 0; local_8 < *(int *)(this + 0x10); local_8 = local_8 + 1) {
          *(undefined4 *)(*(int *)(this + 0x20) + local_8 * 4) =
               *(undefined4 *)(*(int *)(param_1 + 0x20) + local_8 * 4);
        }
      }
    }
  }
  return this;
}

//===== 0x10015067 =====

/* public: __thiscall LMConvert::~LMConvert(void) */

void __thiscall LMConvert::~LMConvert(LMConvert *this)

{
                    /* 0x15067  34  ??1LMConvert@@QAE@XZ */
  release(this);
  return;
}

//===== 0x1001507a =====

/* private: void __thiscall LMConvert::release(void) */

void __thiscall LMConvert::release(LMConvert *this)

{
                    /* 0x1507a  333  ?release@LMConvert@@AAEXXZ */
  if (*(int *)(this + 0x1c) != 0) {
    operator_delete(*(void **)(this + 0x1c));
  }
  if (*(int *)(this + 0x20) != 0) {
    operator_delete(*(void **)(this + 0x20));
  }
  if (*(int *)(this + 0x18) != 0) {
    operator_delete(*(void **)(this + 0x18));
  }
  *(undefined4 *)(this + 0x1c) = 0;
  *(undefined4 *)(this + 0x20) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  return;
}

//===== 0x100150ff =====

/* public: void __thiscall LMConvert::debug(void)const  */

void __thiscall LMConvert::debug(LMConvert *this)

{
  int local_8;
  
                    /* 0x150ff  125  ?debug@LMConvert@@QBEXXZ */
  printf(s_LMConvert____p_1003f7c4);
  printf(s_m_npts___3d_1003f7d4);
  printf(s_m_l___3d_1003f7e4);
  printf(s_m_m___3d_1003f7f4);
  printf(s_m_nout___3d_1003f804);
  printf(s_m_ninc___3d_1003f814);
  printf(s_m_ncoef__3d_1003f824);
  printf(s_m_inc__1003f834);
  for (local_8 = 0; local_8 < *(int *)(this + 0xc); local_8 = local_8 + 1) {
    printf(s__2d_1003f840);
  }
  printf(s_m_coef__1003f848);
  for (local_8 = 0; local_8 < *(int *)(this + 0x10) / 2; local_8 = local_8 + 1) {
    printf(s__4_2f__4_2f_1003f854,(double)*(float *)(*(int *)(this + 0x20) + local_8 * 8),
           (double)*(float *)(*(int *)(this + 0x20) + 4 + local_8 * 8));
  }
  printf(s_m_outp__1003f864);
  for (local_8 = 0; local_8 < *(int *)(this + 0x14); local_8 = local_8 + 1) {
    printf(s__7_1f_1003f870,(double)*(float *)(*(int *)(this + 0x18) + local_8 * 4));
  }
  return;
}

//===== 0x100152a0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 * __thiscall FUN_100152a0(void *this,int param_1)

{
  undefined4 uVar1;
  double dVar2;
  int local_14;
  int local_8;
  
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0x3ff00000;
  *(undefined4 *)((int)this + 0x30) = 0;
  *(undefined4 *)((int)this + 0x1c060) = 0;
  FUN_10015669(this,param_1);
  if (param_1 == 0) {
    dVar2 = log((double)CONCAT44(DAT_1003897c,DAT_10038978));
    dVar2 = sqrt(dVar2 / _DAT_10038980);
    dVar2 = dVar2 * _DAT_10038988;
    for (local_14 = 1; local_14 < 0x22; local_14 = local_14 + 1) {
      uVar1 = ftol(this,dVar2);
      *(undefined4 *)((int)this + (local_14 + 0x7019) * 4) = uVar1;
      if (200 < *(int *)((int)this + (local_14 + 0x7019) * 4)) {
        *(undefined4 *)((int)this + (local_14 + 0x7019) * 4) = 200;
      }
    }
  }
  else {
    dVar2 = log((double)CONCAT44(DAT_10038974,DAT_10038970));
    sqrt(dVar2 / _DAT_10038980);
    for (local_8 = 1; local_8 < 0x22; local_8 = local_8 + 1) {
      uVar1 = ftol();
      *(undefined4 *)((int)this + (local_8 + 0x7019) * 4) = uVar1;
      if (0xaf < *(int *)((int)this + (local_8 + 0x7019) * 4)) {
        *(undefined4 *)((int)this + (local_8 + 0x7019) * 4) = 0xaf;
      }
    }
  }
  return this;
}

//===== 0x1001543a =====

void FUN_1001543a(void)

{
  return;
}

//===== 0x10015445 =====

undefined4 * __thiscall FUN_10015445(void *this,undefined4 *param_1)

{
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0x3ff00000;
  *(undefined4 *)((int)this + 0x30) = 0;
  *(undefined4 *)((int)this + 0x1c060) = 0;
  FUN_10015488(this,param_1);
  return this;
}

//===== 0x10015488 =====

undefined4 * __thiscall FUN_10015488(void *this,undefined4 *param_1)

{
  int local_c;
  int local_8;
  
  *(undefined4 *)((int)this + 0x1c060) = param_1[0x7018];
  local_c = 1;
  for (local_8 = 1; local_8 < 0x801; local_8 = local_8 + 1) {
    *(undefined4 *)((int)this + local_c * 8 + 0x38) = param_1[local_c * 2 + 0xe];
    *(undefined4 *)((int)this + local_c * 8 + 0x3c) = param_1[local_c * 2 + 0xf];
    *(undefined4 *)((int)this + local_c * 8 + 0x40) = param_1[local_c * 2 + 0x10];
    *(undefined4 *)((int)this + local_c * 8 + 0x44) = param_1[local_c * 2 + 0x11];
    *(undefined4 *)((int)this + local_c * 8 + 0x8040) = param_1[local_c * 2 + 0x2010];
    *(undefined4 *)((int)this + local_c * 8 + 0x8044) = param_1[local_c * 2 + 0x2011];
    *(undefined4 *)((int)this + local_c * 8 + 0x8048) = param_1[local_c * 2 + 0x2012];
    *(undefined4 *)((int)this + local_c * 8 + 0x804c) = param_1[local_c * 2 + 0x2013];
    *(undefined4 *)((int)this + local_8 * 8 + 82000) = param_1[local_8 * 2 + 0x5014];
    *(undefined4 *)((int)this + local_8 * 8 + 0x14054) = param_1[local_8 * 2 + 0x5015];
    *(undefined4 *)((int)this + local_8 * 8 + 0x10048) = param_1[local_8 * 2 + 0x4012];
    *(undefined4 *)((int)this + local_8 * 8 + 0x1004c) = param_1[local_8 * 2 + 0x4013];
    *(undefined4 *)((int)this + local_8 * 8 + 0x18058) = param_1[local_8 * 2 + 0x6016];
    *(undefined4 *)((int)this + local_8 * 8 + 0x1805c) = param_1[local_8 * 2 + 0x6017];
    local_c = local_c + 2;
  }
  *(undefined4 *)this = *param_1;
  *(undefined4 *)((int)this + 4) = param_1[1];
  *(undefined4 *)((int)this + 0x30) = param_1[0xc];
  for (local_8 = 0; local_8 < 5; local_8 = local_8 + 1) {
    *(undefined4 *)((int)this + local_8 * 8 + 8) = param_1[local_8 * 2 + 2];
    *(undefined4 *)((int)this + local_8 * 8 + 0xc) = param_1[local_8 * 2 + 3];
  }
  for (local_8 = 1; local_8 < 0x22; local_8 = local_8 + 1) {
    *(undefined4 *)((int)this + local_8 * 4 + 0x1c064) = param_1[local_8 + 0x7019];
  }
  return this;
}

//===== 0x10015669 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __thiscall FUN_10015669(void *this,int param_1)

{
  double *pdVar1;
  double *pdVar2;
  double dVar3;
  double dVar4;
  double dVar5;
  int local_24;
  int local_20;
  uint uStack_18;
  uint uStack_10;
  
  *(undefined4 *)((int)this + 0x1c060) = 0;
  *(undefined4 *)((int)this + 0x18050) = 0;
  *(undefined4 *)((int)this + 0x18054) = 0;
  *(undefined4 *)((int)this + 0x14058) = 0;
  *(undefined4 *)((int)this + 0x1405c) = 0;
  *(undefined4 *)((int)this + 0x16058) = 0;
  *(undefined4 *)((int)this + 0x1605c) = 0x3ff00000;
  if (param_1 == 0) {
    uStack_10 = 0x402a0000;
    uStack_18 = 0x40370000;
  }
  else {
    uStack_10 = 0x401c0000;
    uStack_18 = 0x40380000;
  }
  dVar3 = _DAT_10041e38 /
          ((double)((ulonglong)uStack_18 << 0x20) - (double)((ulonglong)uStack_10 << 0x20));
  dVar4 = _DAT_10041e38 / _DAT_10038988;
  for (local_20 = 2; local_20 < 0x401; local_20 = local_20 + 1) {
    if ((double)((ulonglong)uStack_10 << 0x20) <= (double)local_20) {
      if (((double)local_20 < (double)((ulonglong)uStack_10 << 0x20)) ||
         ((double)((ulonglong)uStack_18 << 0x20) < (double)local_20)) {
        *(undefined4 *)((int)this + local_20 * 8 + 82000) = 0;
        *(undefined4 *)((int)this + local_20 * 8 + 0x14054) = 0x3ff00000;
      }
      else {
        dVar5 = sin((double)local_20 * dVar3 +
                    (dVar4 - dVar3 * (double)((ulonglong)uStack_18 << 0x20)));
        *(double *)((int)this + local_20 * 8 + 82000) = (dVar5 + _DAT_100389a0) * _DAT_10038998;
      }
    }
    else {
      *(undefined4 *)((int)this + local_20 * 8 + 82000) = 0;
      *(undefined4 *)((int)this + local_20 * 8 + 0x14054) = 0;
    }
    *(undefined4 *)((int)this + (0x800 - local_20) * 8 + 0x14060) =
         *(undefined4 *)((int)this + local_20 * 8 + 82000);
    *(undefined4 *)((int)this + (0x800 - local_20) * 8 + 0x14064) =
         *(undefined4 *)((int)this + local_20 * 8 + 0x14054);
  }
  for (local_24 = 1; local_24 < 0x401; local_24 = local_24 + 1) {
    pdVar1 = (double *)((int)this + local_24 * 8 + 0x1a058);
    pdVar2 = (double *)((int)this + local_24 * 8 + 0x18058);
    *pdVar1 = ((double)(local_24 + -1) - _DAT_100389a8) *
              ((_DAT_10038988 * _DAT_10041e38) / _DAT_10038990);
    *pdVar2 = (double)(local_24 + -1) * ((_DAT_10038988 * _DAT_10041e38) / _DAT_10038990);
    *pdVar1 = *pdVar1 * *pdVar1;
    *pdVar2 = *pdVar2 * *pdVar2;
  }
  return;
}

//===== 0x100158ca =====

undefined4 FUN_100158ca(void)

{
  return 1;
}

//===== 0x100158da =====

void FUN_100158da(void)

{
  FUN_100158e4();
  return;
}

//===== 0x100158e4 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_100158e4(void)

{
  _DAT_10041e38 = acos(-1.0);
  return;
}

//===== 0x10015900 =====

/* public: __thiscall BandStat::BandStat(void) */

BandStat * __thiscall BandStat::BandStat(BandStat *this)

{
                    /* 0x15900  4  ??0BandStat@@QAE@XZ */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x1c) = 0x3f800000;
  *(undefined4 *)(this + 0x20) = 0;
  *(undefined4 *)(this + 0x24) = 0x3f800000;
  *(undefined4 *)(this + 0x28) = 0;
  *(undefined4 *)(this + 0x2c) = 0x3f000000;
  *(undefined4 *)(this + 0x30) = 0x3f000000;
  this[0x34] = (BandStat)0x58;
  *(undefined4 *)(this + 0x38) = 0x3f000000;
  *(undefined4 *)(this + 0x3c) = 0;
  *(undefined4 *)(this + 0x4c) = 0;
  *(undefined4 *)(this + 0x48) = 0;
  *(undefined4 *)(this + 0x44) = 0;
  *(undefined4 *)(this + 0x40) = 0;
  return this;
}

//===== 0x100159d2 =====

/* public: void __thiscall BandStat::debug(void)const  */

void __thiscall BandStat::debug(BandStat *this)

{
                    /* 0x159d2  123  ?debug@BandStat@@QBEXXZ */
  printf(s__3d__4d__4d__4d__5_2f__5_2f__4_2_1003f914,*(undefined4 *)this,*(undefined4 *)(this + 8),
         *(undefined4 *)(this + 4),*(undefined4 *)(this + 0xc),(double)*(float *)(this + 0x14),
         (double)*(float *)(this + 0x18),(double)*(float *)(this + 0x1c),
         (double)*(float *)(this + 0x24),(double)*(float *)(this + 0x20),
         (double)*(float *)(this + 0x28),(double)*(float *)(this + 0x2c),
         (double)*(float *)(this + 0x30),(double)*(float *)(this + 0x38),
         *(undefined4 *)(this + 0x10),(double)*(float *)(this + 0x3c),(int)(char)this[0x34]);
  return;
}

//===== 0x10015a8d =====

/* public: void __thiscall BandStatArray::debug(void)const  */

void __thiscall BandStatArray::debug(BandStatArray *this)

{
  int local_8;
  
                    /* 0x15a8d  124  ?debug@BandStatArray@@QBEXXZ */
  printf(s_BandStatArray____p_1003f968,this);
  printf(s_nt__bbgn_bmid_bend_hght_lowv_xbn_1003f97c);
  for (local_8 = 0; local_8 < *(int *)this; local_8 = local_8 + 1) {
    BandStat::debug((BandStat *)(local_8 * 0x50 + *(int *)(this + 4)));
  }
  return;
}

//===== 0x10015aeb =====

/* public: __thiscall BandStatArray::BandStatArray(void) */

BandStatArray * __thiscall BandStatArray::BandStatArray(BandStatArray *this)

{
                    /* 0x15aeb  6  ??0BandStatArray@@QAE@XZ */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  return this;
}

//===== 0x10015b0c =====

/* public: __thiscall BandStatArray::BandStatArray(class BandStatArray const &) */

BandStatArray * __thiscall BandStatArray::BandStatArray(BandStatArray *this,BandStatArray *param_1)

{
                    /* 0x15b0c  5  ??0BandStatArray@@QAE@ABV0@@Z */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  operator=(this,param_1);
  return this;
}

//===== 0x10015b3b =====

/* public: void __thiscall BandStatArray::init(int) */

void __thiscall BandStatArray::init(BandStatArray *this,int param_1)

{
  int *local_30;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x15b3b  239  ?init@BandStatArray@@QAEXH@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036fdb;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  if (*(int *)(this + 4) != 0) {
    ExceptionList = &local_10;
    if (*(void **)(this + 4) != (void *)0x0) {
      ExceptionList = &local_10;
      FUN_10016080(*(void **)(this + 4),3);
    }
    *(undefined4 *)(this + 4) = 0;
    *(undefined4 *)this = 0;
  }
  *(int *)this = param_1;
  local_30 = operator_new(param_1 * 0x50 + 4);
  local_8 = 0;
  if (local_30 == (int *)0x0) {
    local_30 = (int *)0x0;
  }
  else {
    *local_30 = param_1;
    FUN_10036a10(local_30 + 1,0x50,param_1,BandStat::BandStat);
    local_30 = local_30 + 1;
  }
  *(int **)(this + 4) = local_30;
  ExceptionList = local_10;
  return;
}

//===== 0x10015c2c =====

/* public: class BandStatArray const & __thiscall BandStatArray::operator=(class BandStatArray const
   &) */

BandStatArray * __thiscall BandStatArray::operator=(BandStatArray *this,BandStatArray *param_1)

{
  int iVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  int local_8;
  
                    /* 0x15c2c  45  ??4BandStatArray@@QAEABV0@ABV0@@Z */
  if (this != param_1) {
    init(this,*(int *)param_1);
    if (*(int *)(this + 4) == 0) {
      *(undefined4 *)this = 0;
    }
    else {
      for (local_8 = 0; local_8 < *(int *)this; local_8 = local_8 + 1) {
        puVar2 = (undefined4 *)(*(int *)(param_1 + 4) + local_8 * 0x50);
        puVar3 = (undefined4 *)(*(int *)(this + 4) + local_8 * 0x50);
        for (iVar1 = 0x14; iVar1 != 0; iVar1 = iVar1 + -1) {
          *puVar3 = *puVar2;
          puVar2 = puVar2 + 1;
          puVar3 = puVar3 + 1;
        }
      }
    }
  }
  return this;
}

//===== 0x10015cad =====

/* public: __thiscall BandStatArray::~BandStatArray(void) */

void __thiscall BandStatArray::~BandStatArray(BandStatArray *this)

{
                    /* 0x15cad  32  ??1BandStatArray@@QAE@XZ */
  if (*(int *)(this + 4) != 0) {
    if (*(void **)(this + 4) != (void *)0x0) {
      FUN_10016080(*(void **)(this + 4),3);
    }
    *(undefined4 *)(this + 4) = 0;
    *(undefined4 *)this = 0;
  }
  return;
}

//===== 0x10015d01 =====

/* public: void __thiscall BandStatArray::append(class BandStatArray const &,int,int) */

void __thiscall
BandStatArray::append(BandStatArray *this,BandStatArray *param_1,int param_2,int param_3)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  int *piVar6;
  int *local_48;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x15d01  71  ?append@BandStatArray@@QAEXABV1@HH@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10036ff0;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  iVar1 = Wvfm::annotate((Wvfm *)param_1);
  iVar2 = posn(this,param_2);
  iVar3 = posn(param_1,param_3 + -1);
  iVar2 = iVar2 - iVar3;
  *(int *)this = ((param_2 + iVar1) - param_3) + 1;
  iVar3 = *(int *)this;
  local_48 = operator_new(iVar3 * 0x50 + 4);
  local_8 = 0;
  if (local_48 == (int *)0x0) {
    local_48 = (int *)0x0;
  }
  else {
    *local_48 = iVar3;
    FUN_10036a10(local_48 + 1,0x50,iVar3,BandStat::BandStat);
    local_48 = local_48 + 1;
  }
  local_8 = 0xffffffff;
  for (local_14 = 0; local_14 < param_2; local_14 = local_14 + 1) {
    piVar5 = (int *)(*(int *)(this + 4) + local_14 * 0x50);
    piVar6 = local_48 + local_14 * 0x14;
    for (iVar3 = 0x14; iVar3 != 0; iVar3 = iVar3 + -1) {
      *piVar6 = *piVar5;
      piVar5 = piVar5 + 1;
      piVar6 = piVar6 + 1;
    }
  }
  iVar3 = ntnr(param_1,param_3 + -1);
  for (local_18 = param_3 + -1; local_18 < iVar1; local_18 = local_18 + 1) {
    piVar5 = (int *)(*(int *)(param_1 + 4) + local_18 * 0x50);
    piVar6 = local_48 + local_14 * 0x14;
    for (iVar4 = 0x14; iVar4 != 0; iVar4 = iVar4 + -1) {
      *piVar6 = *piVar5;
      piVar5 = piVar5 + 1;
      piVar6 = piVar6 + 1;
    }
    iVar4 = SW::alignedLength((SW *)(local_48 + local_14 * 0x14));
    BandStat::bbgn((BandStat *)(local_48 + local_14 * 0x14),iVar2 + iVar4);
    iVar4 = Annotate::getNumCurrFix((Annotate *)(local_48 + local_14 * 0x14));
    RdrOut::iS1((RdrOut *)(local_48 + local_14 * 0x14),iVar2 + iVar4);
    iVar4 = SSNODE::SWold((SSNODE *)(local_48 + local_14 * 0x14));
    SSNODE::SWold((SSNODE *)(local_48 + local_14 * 0x14),iVar2 + iVar4);
    iVar4 = Wvfm::annotate((Wvfm *)(local_48 + local_14 * 0x14));
    Wvfm::annotate((Wvfm *)(local_48 + local_14 * 0x14),((param_2 + iVar4) - iVar3) + 1);
    local_14 = local_14 + 1;
  }
  if (*(void **)(this + 4) != (void *)0x0) {
    FUN_10016080(*(void **)(this + 4),3);
  }
  *(int **)(this + 4) = local_48;
  ExceptionList = local_10;
  return;
}

//===== 0x10015f59 =====

/* public: void __thiscall BandStatArray::upSmpl(int) */

void __thiscall BandStatArray::upSmpl(BandStatArray *this,int param_1)

{
  int iVar1;
  SW *this_00;
  int local_8;
  
                    /* 0x15f59  429  ?upSmpl@BandStatArray@@QAEXH@Z */
  local_8 = 0;
  while( true ) {
    iVar1 = Wvfm::annotate((Wvfm *)this);
    if (iVar1 <= local_8) break;
    this_00 = (SW *)(*(int *)(this + 4) + local_8 * 0x50);
    iVar1 = SW::alignedLength(this_00);
    BandStat::bbgn((BandStat *)this_00,iVar1 * param_1);
    iVar1 = Annotate::getNumCurrFix((Annotate *)this_00);
    RdrOut::iS1((RdrOut *)this_00,iVar1 * param_1);
    iVar1 = SSNODE::SWold((SSNODE *)this_00);
    SSNODE::SWold((SSNODE *)this_00,iVar1 * param_1);
    local_8 = local_8 + 1;
  }
  return;
}

//===== 0x10015fd9 =====

/* public: void __thiscall BandStatArray::dnSmpl(int) */

void __thiscall BandStatArray::dnSmpl(BandStatArray *this,int param_1)

{
  int iVar1;
  SW *this_00;
  int local_8;
  
                    /* 0x15fd9  142  ?dnSmpl@BandStatArray@@QAEXH@Z */
  local_8 = 0;
  while( true ) {
    iVar1 = Wvfm::annotate((Wvfm *)this);
    if (iVar1 <= local_8) break;
    this_00 = (SW *)(*(int *)(this + 4) + local_8 * 0x50);
    iVar1 = SW::alignedLength(this_00);
    BandStat::bbgn((BandStat *)this_00,iVar1 / param_1);
    iVar1 = Annotate::getNumCurrFix((Annotate *)this_00);
    RdrOut::iS1((RdrOut *)this_00,iVar1 / param_1);
    iVar1 = SSNODE::SWold((SSNODE *)this_00);
    SSNODE::SWold((SSNODE *)this_00,iVar1 / param_1);
    local_8 = local_8 + 1;
  }
  return;
}

//===== 0x10016059 =====

void FUN_10016059(void)

{
  FUN_10016063();
  return;
}

//===== 0x10016063 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10016063(void)

{
  _DAT_10041ea0 = acos(-1.0);
  return;
}

//===== 0x10016080 =====

BandStat * __thiscall FUN_10016080(void *this,uint param_1)

{
  if ((param_1 & 2) == 0) {
    BandStat::~BandStat(this);
    if ((param_1 & 1) != 0) {
      operator_delete(this);
    }
  }
  else {
    FUN_10036ab0(this,0x50,*(int *)((int)this + -4),BandStat::~BandStat);
    operator_delete((void *)((int)this + -4));
  }
  return this;
}

//===== 0x100160e0 =====

/* public: __thiscall Mobility::Mobility(class Wvfm &,int) */

Mobility * __thiscall Mobility::Mobility(Mobility *this,Wvfm *param_1,int param_2)

{
  int iVar1;
  float **ppfVar2;
  void *pvVar3;
  char *pcVar4;
  undefined4 *puVar5;
  int iVar6;
  undefined4 *puVar7;
  double dVar8;
  int local_40;
  short local_3c;
  short local_38;
  int local_30;
  short local_2c;
  int local_24;
  short local_20;
  short local_1c;
  int local_18;
  short local_14;
  short local_10;
  short local_c;
  short local_8;
  
                    /* 0x160e0  11  ??0Mobility@@QAE@AAVWvfm@@H@Z */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(int *)(this + 8) = param_2;
  *(undefined4 *)(this + 0xc) = 0x271;
  *(undefined4 *)(this + 0x10) = 0;
  *(Wvfm **)(this + 0x14) = param_1;
  iVar1 = Wvfm::bgni(*(Wvfm **)(this + 0x14));
  iVar6 = *(int *)(this + 8);
  ppfVar2 = matrix(1,4,1,*(long *)(this + 8));
  *(float ***)this = ppfVar2;
  ppfVar2 = matrix(1,4,1,*(long *)(this + 8));
  *(float ***)(this + 4) = ppfVar2;
  pvVar3 = operator_new((*(int *)(this + 0xc) + 1) * 0x24);
  *(void **)(this + 0x10) = pvVar3;
  if (((*(int *)(this + 0x10) == 0) || (*(int *)(this + 4) == 0)) || (*(int *)(this + 0x10) == 0)) {
    release_(this);
  }
  else {
    for (local_40 = 1; local_40 < 5; local_40 = local_40 + 1) {
      pcVar4 = Wvfm::lnordr(param_1);
      if (pcVar4[local_40 + -1] == 'T') {
        DAT_1003fa1c = local_40 + -1;
        break;
      }
    }
    for (local_40 = 1; local_18 = iVar1, local_40 < 5; local_40 = local_40 + 1) {
      for (; local_18 <= iVar1 + -1 + iVar6; local_18 = local_18 + 1) {
        dVar8 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_18,local_40);
        *(float *)(*(int *)(*(int *)this + local_40 * 4) + 4 + (local_18 - iVar1) * 4) =
             (float)dVar8;
        dVar8 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_18,local_40);
        *(float *)(*(int *)(*(int *)(this + 4) + local_40 * 4) + 4 + (local_18 - iVar1) * 4) =
             (float)dVar8;
      }
    }
    local_20 = 0;
    for (local_3c = 0; local_3c < 5; local_3c = local_3c + 1) {
      for (local_2c = 0; local_2c < 1; local_2c = local_2c + 1) {
        for (local_8 = 0; local_8 < 5; local_8 = local_8 + 1) {
          for (local_38 = 0; local_38 < 1; local_38 = local_38 + 1) {
            for (local_c = 0; local_c < 5; local_c = local_c + 1) {
              for (local_14 = 0; local_14 < 1; local_14 = local_14 + 1) {
                for (local_10 = 0; local_10 < 5; local_10 = local_10 + 1) {
                  for (local_1c = 0; local_1c < 1; local_1c = local_1c + 1) {
                    puVar5 = (undefined4 *)(*(int *)(this + 0x10) + local_20 * 0x24);
                    *puVar5 = *(undefined4 *)(&DAT_100389c0 + local_3c * 4);
                    puVar5[1] = *(undefined4 *)(&DAT_100389d4 + local_2c * 4);
                    puVar5[2] = *(undefined4 *)(&DAT_100389c0 + local_8 * 4);
                    puVar5[3] = *(undefined4 *)(&DAT_100389d4 + local_38 * 4);
                    puVar5[4] = *(undefined4 *)(&DAT_100389c0 + local_c * 4);
                    puVar5[5] = *(undefined4 *)(&DAT_100389d4 + local_14 * 4);
                    puVar5[6] = *(undefined4 *)(&DAT_100389c0 + local_10 * 4);
                    puVar5[7] = *(undefined4 *)(&DAT_100389d4 + local_1c * 4);
                    puVar5[8] = 0;
                    sumEnvLite_(this,(int)local_20);
                    local_20 = local_20 + 1;
                  }
                }
              }
            }
          }
        }
      }
    }
    qsort(*(void **)(this + 0x10),*(size_t *)(this + 0xc),0x24,FUN_10016523);
    local_24 = 0;
    for (local_30 = 1; local_30 < *(int *)(this + 0xc); local_30 = local_30 + 1) {
      if (*(float *)(*(int *)(this + 0x10) + 0x20 + local_24 * 0x24) !=
          *(float *)(*(int *)(this + 0x10) + 0x20 + local_30 * 0x24)) {
        local_24 = local_24 + 1;
        puVar5 = (undefined4 *)(*(int *)(this + 0x10) + local_30 * 0x24);
        puVar7 = (undefined4 *)(*(int *)(this + 0x10) + local_24 * 0x24);
        for (iVar6 = 9; iVar6 != 0; iVar6 = iVar6 + -1) {
          *puVar7 = *puVar5;
          puVar5 = puVar5 + 1;
          puVar7 = puVar7 + 1;
        }
      }
    }
    *(undefined4 *)(this + 0xc) = 10;
  }
  return this;
}

//===== 0x10016523 =====

undefined4 __cdecl FUN_10016523(int param_1,int param_2)

{
  undefined4 local_8;
  
  local_8 = 0;
  if (*(float *)(param_1 + 0x20) <= *(float *)(param_2 + 0x20)) {
    if (*(float *)(param_1 + 0x20) < *(float *)(param_2 + 0x20)) {
      local_8 = 1;
    }
  }
  else {
    local_8 = 0xffffffff;
  }
  return local_8;
}

//===== 0x10016579 =====

/* public: __thiscall Mobility::Mobility(class Mobility const &) */

Mobility * __thiscall Mobility::Mobility(Mobility *this,Mobility *param_1)

{
                    /* 0x16579  12  ??0Mobility@@QAE@ABV0@@Z */
  operator=(this,param_1);
  return this;
}

//===== 0x10016595 =====

/* public: class Mobility const & __thiscall Mobility::operator=(class Mobility const &) */

Mobility * __thiscall Mobility::operator=(Mobility *this,Mobility *param_1)

{
  void *pvVar1;
  float **ppfVar2;
  int iVar3;
  undefined4 *puVar4;
  undefined4 *puVar5;
  int local_c;
  int local_8;
  
                    /* 0x16595  48  ??4Mobility@@QAEABV0@ABV0@@Z */
  if (param_1 != this) {
    release_(this);
    *(undefined4 *)(this + 0xc) = *(undefined4 *)(param_1 + 0xc);
    pvVar1 = operator_new(*(int *)(this + 0xc) * 0x24);
    *(void **)(this + 0x10) = pvVar1;
    *(undefined4 *)(this + 8) = *(undefined4 *)(param_1 + 8);
    ppfVar2 = matrix(1,4,1,*(long *)(this + 8));
    *(float ***)this = ppfVar2;
    *(undefined4 *)(this + 8) = *(undefined4 *)(param_1 + 8);
    ppfVar2 = matrix(1,4,1,*(long *)(this + 8));
    *(float ***)(this + 4) = ppfVar2;
    if (((*(int *)(this + 0x10) == 0) || (*(int *)this == 0)) || (*(int *)(this + 4) == 0)) {
      release_(this);
    }
    else {
      for (local_8 = 0; local_8 < *(int *)(this + 0xc); local_8 = local_8 + 1) {
        puVar4 = (undefined4 *)(*(int *)(param_1 + 0x10) + local_8 * 0x24);
        puVar5 = (undefined4 *)(*(int *)(this + 0x10) + local_8 * 0x24);
        for (iVar3 = 9; iVar3 != 0; iVar3 = iVar3 + -1) {
          *puVar5 = *puVar4;
          puVar4 = puVar4 + 1;
          puVar5 = puVar5 + 1;
        }
      }
      for (local_8 = 1; local_8 < 5; local_8 = local_8 + 1) {
        for (local_c = 1; local_c <= *(int *)(this + 8); local_c = local_c + 1) {
          *(undefined4 *)(*(int *)(*(int *)this + local_8 * 4) + local_c * 4) =
               *(undefined4 *)(*(int *)(*(int *)param_1 + local_8 * 4) + local_c * 4);
          *(undefined4 *)(*(int *)(*(int *)(this + 4) + local_8 * 4) + local_c * 4) =
               *(undefined4 *)(*(int *)(*(int *)(param_1 + 4) + local_8 * 4) + local_c * 4);
        }
      }
    }
  }
  return this;
}

//===== 0x10016718 =====

/* private: void __thiscall Mobility::release_(void) */

void __thiscall Mobility::release_(Mobility *this)

{
                    /* 0x16718  337  ?release_@Mobility@@AAEXXZ */
  if (*(int *)this != 0) {
    free_matrix(*(float ***)this,1,4,1,*(long *)(this + 8));
    *(undefined4 *)this = 0;
  }
  if (*(int *)(this + 4) != 0) {
    free_matrix(*(float ***)(this + 4),1,4,1,*(long *)(this + 8));
    *(undefined4 *)(this + 4) = 0;
  }
  if (*(int *)(this + 0x10) != 0) {
    operator_delete(*(void **)(this + 0x10));
    *(undefined4 *)(this + 0x10) = 0;
  }
  return;
}

//===== 0x100167a8 =====

/* public: __thiscall Mobility::~Mobility(void) */

void __thiscall Mobility::~Mobility(Mobility *this)

{
                    /* 0x167a8  35  ??1Mobility@@QAE@XZ */
  release_(this);
  return;
}

//===== 0x100167bb =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Mobility::warpTrace_(int,int,int * *) */

void __thiscall Mobility::warpTrace_(Mobility *this,int param_1,int param_2,int **param_3)

{
  int iVar1;
  float fVar2;
  float fVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  double dVar8;
  int local_44;
  float local_30 [4];
  float local_20 [4];
  int local_10;
  float *local_c;
  int local_8;
  
                    /* 0x167bb  434  ?warpTrace_@Mobility@@AAEXHHPAPAH@Z */
  local_c = (float *)(*(int *)(this + 0x10) + param_1 * 0x24);
  if (param_3 != (int **)0x0) {
    for (local_8 = 1; local_8 < 5; local_8 = local_8 + 1) {
      for (local_10 = 1; local_10 <= *(int *)(this + 8); local_10 = local_10 + 1) {
        param_3[local_8][local_10] = 0;
      }
    }
  }
  local_20[0] = *local_c;
  local_20[1] = local_c[2];
  local_20[2] = local_c[4];
  local_30[0] = local_c[1];
  local_30[1] = local_c[3];
  local_30[2] = local_c[5];
  local_20[3] = local_c[6];
  local_30[3] = local_c[7];
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    local_44 = -1;
    iVar7 = local_8 + 1;
    if ((DAT_1003fa1c != local_8) && (fVar3 = local_20[local_8], fVar3 != _DAT_100389dc)) {
      iVar1 = *(int *)(this + 8);
      fVar2 = local_30[local_8];
      dVar8 = exp((double)-local_30[local_8]);
      if (param_2 == 1) {
        Wvfm::setMCoef(*(Wvfm **)(this + 0x14),local_8,*(int *)(this + 8),fVar3,(float)iVar1 * fVar2
                       ,(float)dVar8);
      }
      for (local_10 = 1; local_10 <= *(int *)(this + 8); local_10 = local_10 + 1) {
        exp((double)(-(float)local_10 / ((float)iVar1 * fVar2)));
        iVar5 = ftol();
        iVar4 = local_44;
        if ((1 < iVar5) && (iVar5 <= *(int *)(this + 8))) {
          if (param_3 != (int **)0x0) {
            param_3[iVar7][local_10] = iVar5 - local_10;
          }
          *(undefined4 *)(*(int *)(*(int *)(this + 4) + iVar7 * 4) + iVar5 * 4) =
               *(undefined4 *)(*(int *)(*(int *)this + iVar7 * 4) + local_10 * 4);
          iVar4 = iVar5;
          if ((local_44 != -1) && (iVar6 = abs(iVar5 - local_44), iVar6 != 1)) {
            *(float *)(*(int *)(*(int *)(this + 4) + iVar7 * 4) + ((iVar5 + local_44) / 2) * 4) =
                 (*(float *)(*(int *)(*(int *)(this + 4) + iVar7 * 4) + iVar5 * 4) +
                 *(float *)(*(int *)(*(int *)(this + 4) + iVar7 * 4) + local_44 * 4)) /
                 _DAT_100389e8;
          }
        }
        local_44 = iVar4;
      }
    }
  }
  return;
}

//===== 0x10016a39 =====

/* private: void __thiscall Mobility::sumEnvLite_(int) */

void __thiscall Mobility::sumEnvLite_(Mobility *this,int param_1)

{
  int iVar1;
  float local_14;
  int local_10;
  int local_c;
  
                    /* 0x16a39  421  ?sumEnvLite_@Mobility@@AAEXH@Z */
  iVar1 = *(int *)(this + 0x10) + param_1 * 0x24;
  warpTrace_(this,param_1,0,(int **)0x0);
  *(undefined4 *)(iVar1 + 0x20) = 0;
  for (local_c = 1; local_c <= *(int *)(this + 8); local_c = local_c + 1) {
    local_14 = *(float *)(*(int *)(*(int *)(this + 4) + 4) + local_c * 4);
    for (local_10 = 2; local_10 < 5; local_10 = local_10 + 1) {
      if (local_14 < *(float *)(*(int *)(*(int *)(this + 4) + local_10 * 4) + local_c * 4)) {
        local_14 = *(float *)(*(int *)(*(int *)(this + 4) + local_10 * 4) + local_c * 4);
      }
    }
    *(float *)(iVar1 + 0x20) = *(float *)(iVar1 + 0x20) + local_14;
  }
  return;
}

//===== 0x10016b01 =====

/* public: int __thiscall Mobility::search(void) */

int __thiscall Mobility::search(Mobility *this)

{
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x16b01  352  ?search@Mobility@@QAEHXZ */
  for (local_10 = 0; local_10 < 0x46; local_10 = local_10 + 1) {
    minmax_(this,&local_c,&local_8);
    ralt_(this,local_c,local_8);
  }
  return 1;
}

//===== 0x10016b4d =====

/* private: void __thiscall Mobility::minmax_(int &,int &)const  */

void __thiscall Mobility::minmax_(Mobility *this,int *param_1,int *param_2)

{
  float fVar1;
  float local_14;
  int local_10;
  float local_c;
  
                    /* 0x16b4d  282  ?minmax_@Mobility@@ABEXAAH0@Z */
  *param_2 = 0;
  *param_1 = 0;
  local_14 = *(float *)(*(int *)(this + 0x10) + 0x20);
  local_c = local_14;
  for (local_10 = 1; local_10 < *(int *)(this + 0xc); local_10 = local_10 + 1) {
    fVar1 = *(float *)(*(int *)(this + 0x10) + 0x20 + local_10 * 0x24);
    if (fVar1 <= local_c) {
      if (fVar1 < local_14) {
        *param_1 = local_10;
        local_14 = fVar1;
      }
    }
    else {
      *param_2 = local_10;
      local_c = fVar1;
    }
  }
  return;
}

//===== 0x10016bea =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Mobility::ralt_(int,int) */

void __thiscall Mobility::ralt_(Mobility *this,int param_1,int param_2)

{
  int iVar1;
  float *pfVar2;
  float *pfVar3;
  float *pfVar4;
  float10 fVar5;
  
                    /* 0x16bea  326  ?ralt_@Mobility@@AAEXHH@Z */
  pfVar2 = (float *)(*(int *)(this + 0x10) + param_1 * 0x24);
  pfVar3 = (float *)(*(int *)(this + 0x10) + param_2 * 0x24);
  pfVar4 = pfVar2;
  for (iVar1 = 9; iVar1 != 0; iVar1 = iVar1 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  if (DAT_1003fa1c != 0) {
    fVar5 = FUN_100186e0();
    *pfVar2 = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) + (float10)*pfVar2);
    fVar5 = FUN_100186e0();
    pfVar2[1] = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) /
                        (float10)_DAT_100389d8 + (float10)pfVar2[1]);
  }
  if (DAT_1003fa1c != 1) {
    fVar5 = FUN_100186e0();
    pfVar2[2] = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) +
                       (float10)pfVar2[2]);
    fVar5 = FUN_100186e0();
    pfVar2[3] = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) /
                        (float10)_DAT_100389d8 + (float10)pfVar2[3]);
  }
  if (DAT_1003fa1c != 2) {
    fVar5 = FUN_100186e0();
    pfVar2[4] = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) +
                       (float10)pfVar2[4]);
    fVar5 = FUN_100186e0();
    pfVar2[5] = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) /
                        (float10)_DAT_100389d8 + (float10)pfVar2[5]);
  }
  if (DAT_1003fa1c != 3) {
    fVar5 = FUN_100186e0();
    pfVar2[6] = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) +
                       (float10)pfVar2[6]);
    fVar5 = FUN_100186e0();
    pfVar2[7] = (float)((fVar5 * (float10)_DAT_100389f0 - (float10)_DAT_100389f8) /
                        (float10)_DAT_100389d8 + (float10)pfVar2[7]);
  }
  sumEnvLite_(this,param_1);
  return;
}

//===== 0x10016d72 =====

void FUN_10016d72(void)

{
  FUN_10016d7c();
  return;
}

//===== 0x10016d7c =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10016d7c(void)

{
  _DAT_10041f08 = acos(-1.0);
  return;
}

//===== 0x10016d96 =====

/* public: void __thiscall Mobility::apply(int * *) */

void __thiscall Mobility::apply(Mobility *this,int **param_1)

{
  int local_18;
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x16d96  73  ?apply@Mobility@@QAEXPAPAH@Z */
  minmax_(this,&local_10,&local_8);
  warpTrace_(this,local_8,1,param_1);
  for (local_14 = 1; local_14 < 5; local_14 = local_14 + 1) {
    local_18 = Wvfm::bgni(*(Wvfm **)(this + 0x14));
    for (local_c = 1; local_c <= *(int *)(this + 8); local_c = local_c + 1) {
      Wvfm::sc_la_set(*(Wvfm **)(this + 0x14),local_18,local_14,
                      (double)*(float *)(*(int *)(*(int *)(this + 4) + local_14 * 4) + local_c * 4))
      ;
      local_18 = local_18 + 1;
    }
  }
  return;
}

//===== 0x10016e42 =====

undefined4 __cdecl FUN_10016e42(int param_1,int param_2)

{
  undefined4 uVar1;
  
  if (*(int *)(param_2 + 4) < *(int *)(param_1 + 4)) {
    uVar1 = 1;
  }
  else if (*(int *)(param_1 + 4) < *(int *)(param_2 + 4)) {
    uVar1 = 0xffffffff;
  }
  else {
    uVar1 = 0;
  }
  return uVar1;
}

//===== 0x10016e7c =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: void __thiscall Mobility::touchUp(void) */

void __thiscall Mobility::touchUp(Mobility *this)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  float fVar4;
  void *_Base;
  int iVar5;
  int *piVar6;
  undefined4 *puVar7;
  int iVar8;
  undefined4 *puVar9;
  double dVar10;
  double dVar11;
  double dVar12;
  int local_e0;
  int local_a0;
  double local_98;
  float local_8c;
  double local_88;
  float local_80;
  float local_74;
  float local_70;
  int local_6c;
  float local_68;
  int local_64;
  undefined4 local_58;
  undefined4 uStack_54;
  int local_4c;
  int local_44;
  int local_40;
  undefined4 local_38;
  undefined4 uStack_34;
  int local_2c;
  size_t local_28;
  int local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  
                    /* 0x16e7c  426  ?touchUp@Mobility@@QAEXXZ */
  _Base = operator_new(0x3840);
  local_28 = 0;
  local_44 = 0;
  iVar5 = Wvfm::bgni(*(Wvfm **)(this + 0x14));
  iVar8 = *(int *)(this + 8);
  local_4c = 1;
  do {
    local_24 = iVar5 + 1;
    if (4 < local_4c) {
      if (1 < (int)local_28) {
        Wvfm::lnordr(*(Wvfm **)(this + 0x14));
        qsort(_Base,local_28,0x30,FUN_10016e42);
        local_70 = 0.0;
        local_68 = 100000.0;
        local_74 = 0.0;
        for (local_40 = 0; local_40 < (int)local_28; local_40 = local_40 + 1) {
          local_74 = local_74 + *(float *)((int)_Base + local_40 * 0x30 + 0x2c);
          if (local_70 < *(float *)((int)_Base + local_40 * 0x30 + 0x2c)) {
            local_70 = *(float *)((int)_Base + local_40 * 0x30 + 0x2c);
          }
          if (*(float *)((int)_Base + local_40 * 0x30 + 0x2c) < local_68) {
            local_68 = *(float *)((int)_Base + local_40 * 0x30 + 0x2c);
          }
        }
        fVar4 = (_DAT_10038a10 * (local_74 / (float)(int)local_28)) / _DAT_100389e8;
        local_6c = 0;
        for (local_64 = 0; local_64 < (int)local_28; local_64 = local_64 + 1) {
          puVar7 = (undefined4 *)((int)_Base + local_64 * 0x30);
          if (fVar4 <= (float)puVar7[0xb]) {
            puVar9 = (undefined4 *)((int)_Base + local_6c * 0x30);
            for (iVar8 = 0xc; iVar8 != 0; iVar8 = iVar8 + -1) {
              *puVar9 = *puVar7;
              puVar7 = puVar7 + 1;
              puVar9 = puVar9 + 1;
            }
            local_6c = local_6c + 1;
          }
        }
        for (local_40 = 2; local_40 < local_6c + -2; local_40 = local_40 + 1) {
          piVar6 = (int *)((int)_Base + local_40 * 0x30);
          local_88 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),piVar6[1] + -1,1);
          local_98 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),piVar6[1] + 1,1);
          local_80 = 0.0;
          local_8c = 0.0;
          for (local_4c = 2; local_4c < 5; local_4c = local_4c + 1) {
            dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),piVar6[1] + -1,local_4c);
            if (local_88 < dVar10) {
              local_88 = dVar10;
            }
            dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),piVar6[1] + 1,local_4c);
            if (local_98 < dVar10) {
              local_98 = dVar10;
            }
          }
          if ((float)local_88 <= (float)piVar6[9] != (float)local_98 <= (float)piVar6[9]) {
            iVar8 = *(int *)((int)_Base + (local_40 + -1) * 0x30 + 8);
            local_a0 = *piVar6;
            while (local_a0 <= iVar8) {
              dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_a0,
                                   *(int *)((int)_Base + (local_40 + -1) * 0x30 + 0xc));
              local_80 = (float)dVar10 + local_80;
              local_a0 = local_a0 + 1;
            }
            iVar8 = piVar6[2];
            local_a0 = *(int *)((int)_Base + (local_40 + 1) * 0x30);
            while (local_a0 <= iVar8) {
              dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_a0,
                                   *(int *)((int)_Base + (local_40 + 1) * 0x30 + 0xc));
              local_8c = (float)dVar10 + local_8c;
              local_a0 = local_a0 + 1;
            }
            if (local_80 <= local_8c) {
              local_e0 = local_40 + 1;
            }
            else {
              local_e0 = local_40;
            }
            uVar1 = *(undefined4 *)((int)_Base + local_e0 * 0x30);
            iVar8 = (*(int *)((int)_Base + local_40 * 0x30 + 8) -
                    *(int *)((int)_Base + local_40 * 0x30)) / 2;
            uVar2 = *(undefined4 *)((int)_Base + (local_e0 + -1) * 0x30 + 0xc);
            uVar3 = *(undefined4 *)((int)_Base + (local_e0 + -1) * 0x30 + 8);
            if (0 < iVar8) {
              local_44 = local_44 + iVar8;
              *(int *)((int)_Base + local_e0 * 0x30 + 0x10) = iVar8;
              *(undefined4 *)((int)_Base + local_e0 * 0x30 + 0x14) = uVar1;
              *(undefined4 *)((int)_Base + local_e0 * 0x30 + 0x18) = uVar2;
              *(undefined4 *)((int)_Base + local_e0 * 0x30 + 0x1c) = uVar3;
            }
          }
        }
        if (local_44 != 0) {
          FUN_100176ed(*(Wvfm **)(this + 0x14),local_44,(int)_Base,local_6c);
        }
      }
      operator_delete(_Base);
      return;
    }
    for (; local_24 <= iVar8 + -1; local_24 = local_24 + 1) {
      dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_24 + -1,local_4c);
      dVar11 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_24,local_4c);
      dVar12 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_24 + 1,local_4c);
      if ((((dVar10 < dVar11) && (dVar12 < dVar11)) && (_DAT_10038a00 < dVar10)) &&
         (_DAT_10038a00 < dVar12)) {
        if (299 < (int)local_28) break;
        piVar6 = (int *)((int)_Base + local_28 * 0x30);
        local_28 = local_28 + 1;
        piVar6[9] = (int)(float)dVar11;
        piVar6[1] = local_24;
        piVar6[3] = local_4c;
        piVar6[4] = 0;
        piVar6[5] = 0;
        piVar6[0xb] = (int)(float)dVar11;
        local_40 = local_24 + -1;
        local_20 = SUB84(dVar11,0);
        local_38 = local_20;
        uStack_1c = (undefined4)((ulonglong)dVar11 >> 0x20);
        uStack_34 = uStack_1c;
        local_2c = local_40;
        while (((iVar5 + 1 < local_40 &&
                (dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_40,local_4c),
                _DAT_10038a08 * dVar11 < dVar10)) &&
               ((dVar10 <= (double)CONCAT44(uStack_34,local_38) && (_DAT_10038a00 <= dVar10))))) {
          piVar6[0xb] = (int)((float)dVar10 + (float)piVar6[0xb]);
          local_58 = SUB84(dVar10,0);
          local_38 = local_58;
          uStack_54 = (undefined4)((ulonglong)dVar10 >> 0x20);
          uStack_34 = uStack_54;
          local_2c = local_40;
          local_40 = local_40 + -1;
        }
        *piVar6 = local_2c;
        dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_2c,local_4c);
        piVar6[8] = (int)(float)dVar10;
        local_40 = local_24 + 1;
        local_38 = local_20;
        uStack_34 = uStack_1c;
        local_2c = local_40;
        while (((local_40 < iVar8 + -1 &&
                (dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_40,local_4c),
                _DAT_10038a08 * dVar11 < dVar10)) &&
               ((dVar10 <= (double)CONCAT44(uStack_34,local_38) && (_DAT_10038a00 <= dVar10))))) {
          piVar6[0xb] = (int)((float)dVar10 + (float)piVar6[0xb]);
          local_58 = SUB84(dVar10,0);
          local_38 = local_58;
          uStack_54 = (undefined4)((ulonglong)dVar10 >> 0x20);
          uStack_34 = uStack_54;
          local_2c = local_40;
          local_40 = local_40 + 1;
        }
        piVar6[2] = local_2c;
        dVar10 = Wvfm::sc_la(*(Wvfm **)(this + 0x14),local_2c,local_4c);
        piVar6[10] = (int)(float)dVar10;
      }
    }
    local_4c = local_4c + 1;
  } while( true );
}

//===== 0x100176ed =====

void __cdecl FUN_100176ed(Wvfm *param_1,int param_2,int param_3,int param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  double **ppdVar6;
  double dVar7;
  int local_38;
  int local_30;
  int local_20;
  int local_18;
  int local_14;
  int local_c;
  
  iVar4 = Wvfm::rows(param_1);
  iVar5 = iVar4 + param_2;
  ppdVar6 = dmatrix(1,iVar5,1,4);
  for (local_18 = 1; local_18 <= iVar4; local_18 = local_18 + 1) {
    for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
      dVar7 = Wvfm::sc_la(param_1,local_18,local_20);
      ppdVar6[local_18][local_20] = dVar7;
    }
  }
  for (local_c = 0; (0 < param_2 && (local_c < param_4)); local_c = local_c + 1) {
    iVar1 = *(int *)(param_3 + 0x10 + local_c * 0x30);
    if (iVar1 != 0) {
      iVar2 = *(int *)(param_3 + 0x14 + local_c * 0x30);
      iVar3 = *(int *)(param_3 + 0x18 + local_c * 0x30);
      for (local_20 = 1; local_30 = local_c, local_20 < 5; local_20 = local_20 + 1) {
        local_38 = iVar2;
        if (iVar3 == local_20) {
          local_38 = *(int *)(param_3 + 0x1c + local_c * 0x30);
        }
        FUN_1001793d((int)ppdVar6,local_20,local_38,iVar1,iVar5);
      }
      while (local_30 = local_30 + 1, local_30 < param_4) {
        if (*(int *)(param_3 + 0x10 + local_30 * 0x30) != 0) {
          *(int *)(param_3 + 0x14 + local_30 * 0x30) =
               *(int *)(param_3 + 0x14 + local_30 * 0x30) + iVar1;
          *(int *)(param_3 + 0x1c + local_30 * 0x30) =
               *(int *)(param_3 + 0x1c + local_30 * 0x30) + iVar1;
        }
      }
      param_2 = param_2 - iVar1;
    }
  }
  local_18 = iVar5 - iVar4;
  for (local_14 = 1; local_18 = local_18 + 1, local_14 <= iVar4; local_14 = local_14 + 1) {
    for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
      Wvfm::sc_la_set(param_1,local_14,local_20,
                      (double)CONCAT44(*(undefined4 *)((int)ppdVar6[local_18] + local_20 * 8 + 4),
                                       *(undefined4 *)(ppdVar6[local_18] + local_20)));
    }
  }
  free_dmatrix(ppdVar6,1,iVar5,1,4);
  return;
}

//===== 0x1001793d =====

void __cdecl FUN_1001793d(int param_1,int param_2,int param_3,int param_4,int param_5)

{
  int iVar1;
  int iVar2;
  undefined4 local_c;
  undefined4 local_8;
  
  local_8 = param_5;
  for (local_c = param_5 - param_4; param_3 <= local_c; local_c = local_c + -1) {
    iVar1 = *(int *)(param_1 + local_c * 4);
    iVar2 = *(int *)(param_1 + local_8 * 4);
    *(undefined4 *)(iVar2 + param_2 * 8) = *(undefined4 *)(iVar1 + param_2 * 8);
    *(undefined4 *)(iVar2 + 4 + param_2 * 8) = *(undefined4 *)(iVar1 + 4 + param_2 * 8);
    local_8 = local_8 + -1;
  }
  for (; local_c < local_8; local_8 = local_8 + -1) {
    iVar1 = *(int *)(param_1 + local_8 * 4);
    *(undefined4 *)(iVar1 + param_2 * 8) = 0;
    *(undefined4 *)(iVar1 + 4 + param_2 * 8) = 0;
  }
  return;
}

//===== 0x100179cc =====

/* public: void __thiscall Mobility::debug(int) */

void __thiscall Mobility::debug(Mobility *this,int param_1)

{
  double dVar1;
  float *pfVar2;
  int local_24;
  int local_20;
  char *local_1c;
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x179cc  126  ?debug@Mobility@@QAEXH@Z */
  printf(s_Mobility____p_1003fa20,this);
  printf(s_m_tablelen__4d_1003fa30,*(undefined4 *)(this + 0xc));
  printf(s_m_scnl___4d_1003fa44,*(undefined4 *)(this + 8));
  minmax_(this,&local_14,&local_8);
  if (param_1 != -1) {
    local_8 = param_1;
  }
  warpTrace_(this,local_8,0,(int **)0x0);
  printf(s_The_Candidate_Coefficient_Sets_1003fa58);
  for (local_10 = 0; local_10 < *(int *)(this + 0xc); local_10 = local_10 + 1) {
    local_1c = &DAT_10041f10;
    pfVar2 = (float *)(*(int *)(this + 0x10) + local_10 * 0x24);
    if (local_10 == local_8) {
      local_1c = &DAT_1003fa78;
    }
    else if (local_10 == local_14) {
      local_1c = s_WORST_1003fa80;
    }
    printf(s__4_2f___5f__4_2f___5f__4_2f___5f_1003fa88,(double)*pfVar2,(double)pfVar2[1],
           (double)pfVar2[2],(double)pfVar2[3],(double)pfVar2[4],(double)pfVar2[5],(double)pfVar2[6]
           ,(double)pfVar2[7],SUB84((double)pfVar2[8],0),(int)((ulonglong)(double)pfVar2[8] >> 0x20)
           ,local_1c);
  }
  printf(s_The_Trace_Section_Under_Consider_1003fac0);
  for (local_c = 1; local_c <= *(int *)(this + 8); local_c = local_c + 1) {
    for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
      dVar1 = (double)*(float *)(*(int *)(*(int *)this + local_20 * 4) + local_c * 4);
      printf(&DAT_1003fae8,SUB84(dVar1,0),(int)((ulonglong)dVar1 >> 0x20));
    }
    printf(&DAT_1003faec);
  }
  fflush((FILE *)(_iob_exref + 0x20));
  printf(s_The_BEST_Warp_Job_1003faf0);
  for (local_c = 1; local_c <= *(int *)(this + 8); local_c = local_c + 1) {
    for (local_24 = 1; local_24 < 5; local_24 = local_24 + 1) {
      dVar1 = (double)*(float *)(*(int *)(*(int *)(this + 4) + local_24 * 4) + local_c * 4);
      printf(&DAT_1003fb04,SUB84(dVar1,0),(int)((ulonglong)dVar1 >> 0x20));
    }
    printf(&DAT_1003fb08);
  }
  fflush((FILE *)(_iob_exref + 0x20));
  return;
}

//===== 0x10017c50 =====

undefined4 __thiscall FUN_10017c50(void *this,int *param_1)

{
  Wvfm *this_00;
  int iVar1;
  undefined4 uVar2;
  size_t _NumOfElements;
  int *piVar3;
  int iVar4;
  int local_18;
  int local_10;
  
  this_00 = (Wvfm *)FUN_10026690((int)this);
  iVar1 = Wvfm::annotate(this_00);
  if (iVar1 < 2) {
    uVar2 = 0;
  }
  else {
    iVar1 = Wvfm::annotate(this_00);
    _NumOfElements = iVar1 - 1;
    piVar3 = ivector(1,_NumOfElements);
    if (piVar3 == (int *)0x0) {
      uVar2 = 0;
    }
    else {
      local_18 = 1;
      for (local_10 = 0; local_10 < (int)_NumOfElements; local_10 = local_10 + 1) {
        iVar1 = BandStatArray::posn((BandStatArray *)this_00,local_18);
        iVar4 = BandStatArray::posn((BandStatArray *)this_00,local_10);
        piVar3[local_18] = iVar1 - iVar4;
        local_18 = local_18 + 1;
      }
      qsort(piVar3 + 1,_NumOfElements,4,FUN_10017d48);
      *param_1 = piVar3[(int)(_NumOfElements * 0x28) / 100];
      free_ivector(piVar3,1,_NumOfElements);
      uVar2 = 1;
    }
  }
  return uVar2;
}

//===== 0x10017d48 =====

int __cdecl FUN_10017d48(int *param_1,int *param_2)

{
  return *param_1 - *param_2;
}

//===== 0x10017d57 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: int __thiscall Wvfm::nfeeder(class RdrOut &,struct TestOptions &,int) */

int __thiscall Wvfm::nfeeder(Wvfm *this,RdrOut *param_1,TestOptions *param_2,int param_3)

{
  int iVar1;
  QualCtrl *pQVar2;
  int iVar3;
  DATASRC DVar4;
  double *pdVar5;
  Wvfm *pWVar6;
  ObsInpSpec *pOVar7;
  Wvfm *this_00;
  Wvfm *pWVar8;
  int local_a898;
  int local_a884;
  int local_a880;
  int local_a87c;
  int local_a878 [4];
  int local_a868 [4];
  int local_a858;
  undefined4 local_a854;
  SegRead local_a850 [43040];
  int local_30;
  int local_2c;
  uint uVar9;
  TAxisChg TVar10;
  uint uVar12;
  undefined8 uVar11;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x17d57  283  ?nfeeder@Wvfm@@QAEHAAVRdrOut@@AAUTestOptions@@H@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003700c;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  FUN_10036c00();
  if ((*(int *)(this_00 + 0xc0) == 0) || (*(int *)(this_00 + 0x168) == 0x14)) {
    *(undefined4 *)(this_00 + 0x168) = 0x14;
    iVar1 = 0;
  }
  else {
    srand(0);
    pQVar2 = RdrOut::qualctrl(param_1);
    QualCtrl::startTimer(pQVar2);
    iVar1 = preproc(this_00,(TestOptions *)&stack0xffffffe0);
    if (iVar1 == 1) {
      if (param_3 == -99) {
        iVar1 = 1;
      }
      else {
        iVar1 = bgni(this_00);
        RdrOut::iS1(param_1,iVar1);
        iVar1 = endi(this_00);
        iVar3 = bgni(this_00);
        if (0x7ff < (iVar1 - iVar3) + 1) {
          ceil((double)((float)((iVar1 - iVar3) + -0x7ff) / _DAT_10038a20));
          ftol();
        }
        DVar4 = ds(this_00);
        uVar12 = (uint)(DVar4 == 3);
        iVar1 = bgni(this_00);
        uVar9 = 0x10017eef;
        FUN_1002497b(local_a850,iVar1,uVar12);
        local_8 = 0;
        local_2c = *(int *)(this_00 + 0x1b0);
        if ((uVar9 >> 2 & 1) == 1) {
          local_a880 = 0;
          local_a87c = 0;
          microBursts(this_00,local_a878,local_a868);
          for (local_a858 = 0; local_a858 < 4; local_a858 = local_a858 + 1) {
            local_a880 = local_a880 + local_a878[local_a858];
            local_a87c = local_a87c + local_a868[local_a858];
          }
          if (local_a87c == 0) {
            local_a898 = *(int *)(this_00 + 0x1b0);
          }
          else {
            local_a898 = (local_a87c + local_a880 * 2) / (local_a87c << 1);
          }
          local_2c = local_a898;
          FUN_100263f4(local_a850,local_a898,&local_a854);
        }
        uVar11 = CONCAT44(&stack0xffffffdc,local_2c);
        FUN_100263f4(local_a850,local_2c,(undefined4 *)&stack0xffffffdc);
        for (local_30 = 1; local_30 <= (int)uVar11; local_30 = local_30 + 1) {
          local_2c = 0x1001805f;
          iVar1 = nreader(this_00,1,1,local_a850,local_30,(TestOptions *)&stack0xffffffe0);
          if (iVar1 == 0) {
            if ((local_30 == 1) && (*(int *)(this_00 + 0x168) == 1)) {
              *(undefined4 *)(this_00 + 0x168) = 0x15;
            }
            break;
          }
          iVar1 = FUN_10017c50(local_a850,&local_2c);
          if (iVar1 == 0) {
            if ((local_30 == 1) && (*(int *)(this_00 + 0x168) == 1)) {
              *(undefined4 *)(this_00 + 0x168) = 0x15;
            }
            break;
          }
          if (local_30 != 1) {
            iVar1 = local_30 + -2;
            pQVar2 = RdrOut::qualctrl(param_1);
            iVar1 = QualCtrl::bspac(pQVar2,iVar1);
            if (((local_30 < 3) || (DVar4 = ds(this_00), DVar4 == 5)) && (local_2c < iVar1)) {
              local_2c = iVar1;
            }
          }
          FUN_100263f4(local_a850,local_2c,(undefined4 *)&stack0xffffffdc);
          iVar3 = 2;
          local_2c = 0x1001817b;
          iVar1 = nreader(this_00,2,2,local_a850,local_30,(TestOptions *)&stack0xffffffe0);
          if (iVar1 == 0) {
            if ((local_30 == 1) && (*(int *)(this_00 + 0x168) == 1)) {
              *(undefined4 *)(this_00 + 0x168) = 0x16;
            }
            break;
          }
          iVar1 = RdrOut::add(param_1,local_30,iVar3,local_2c,local_a850);
          if (iVar1 == 0) {
            if ((local_30 == 1) && (*(int *)(this_00 + 0x168) == 1)) {
              *(undefined4 *)(this_00 + 0x168) = 0x17;
            }
            break;
          }
          iVar1 = Annotate::getNumCurrFix((Annotate *)local_a850);
          local_a884 = iVar1 + 0x76c;
          iVar3 = endi(this_00);
          if (iVar3 <= iVar1 + 0xf6c) {
            local_a884 = endi(this_00);
            local_a884 = local_a884 + -0x800;
          }
          uVar11 = CONCAT44(local_a884,0x1001828b);
          RdrOut::iS1((RdrOut *)local_a850,local_a884);
        }
        pQVar2 = RdrOut::qualctrl(param_1);
        QualCtrl::stopTimer(pQVar2);
        iVar1 = (int)(char)this_00[0x170];
        pdVar5 = ssm(this_00);
        pWVar6 = RdrOut::wvfm(param_1);
        ssm(pWVar6,pdVar5,iVar1);
        pOVar7 = ispec(this_00);
        pWVar6 = RdrOut::wvfm(param_1);
        ispec(pWVar6,pOVar7);
        pWVar8 = this_00 + 4;
        pWVar6 = RdrOut::wvfm(param_1);
        Annotate::operator=((Annotate *)(pWVar6 + 4),(Annotate *)pWVar8);
        pWVar6 = RdrOut::wvfm(param_1);
        iVar1 = rows(pWVar6);
        TVar10 = 5;
        pWVar6 = RdrOut::wvfm(param_1);
        Annotate::setNScnl((Annotate *)(pWVar6 + 4),TVar10,iVar1);
        pWVar6 = RdrOut::wvfm(param_1);
        *(undefined4 *)pWVar6 = *(undefined4 *)this_00;
        pWVar6 = RdrOut::wvfm(param_1);
        *(undefined4 *)(pWVar6 + 0x2f8) = *(undefined4 *)(this_00 + 0x2f8);
        pWVar6 = RdrOut::wvfm(param_1);
        *(undefined4 *)(pWVar6 + 0x2fc) = *(undefined4 *)(this_00 + 0x2fc);
        iVar1 = 0x10018371;
        pWVar6 = RdrOut::wvfm(param_1);
        *(undefined4 *)(pWVar6 + 0x168) = *(undefined4 *)(this_00 + 0x168);
        if ((iVar1 == 0) && (1 < local_30)) {
          iVar1 = 1;
        }
        local_8 = 0xffffffff;
        FUN_10024a62((int)local_a850);
      }
    }
    else {
      if (param_3 != 0) {
        errmsg(this_00);
        fprintf((FILE *)(_iob_exref + 0x40),s_preproc___failed__status__s_1003fb58);
      }
      iVar1 = 0;
    }
  }
  ExceptionList = local_10;
  return iVar1;
}

//===== 0x100183c8 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Wvfm::microBursts(int * const,int * const)const  */

void __thiscall Wvfm::microBursts(Wvfm *this,int *param_1,int *param_2)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  double *pdVar5;
  undefined8 local_40;
  int local_28;
  double local_24;
  undefined4 local_1c;
  undefined4 uStack_18;
  int local_14;
  int local_8;
  
                    /* 0x183c8  280  ?microBursts@Wvfm@@ABEXQAH0@Z */
  iVar1 = *(int *)(this + 0xbc);
  iVar2 = *(int *)(this + 0xb8);
  param_1[3] = 0;
  param_1[2] = 0;
  param_1[1] = 0;
  *param_1 = 0;
  param_2[3] = 0;
  param_2[2] = 0;
  param_2[1] = 0;
  *param_2 = 0;
  pdVar5 = dvector(1,1000);
  if (pdVar5 != (double *)0x0) {
    for (local_14 = 1; local_14 < 5; local_14 = local_14 + 1) {
      for (local_8 = 1; local_8 < 0x3e9; local_8 = local_8 + 1) {
        if ((iVar1 - iVar2) + 1 < local_8) {
          local_40 = 0.0;
        }
        else {
          local_40 = sc_la(this,*(int *)(this + 0xb8) + -1 + local_8,local_14);
        }
        *(undefined4 *)(pdVar5 + local_8) = (undefined4)local_40;
        *(undefined4 *)((int)pdVar5 + local_8 * 8 + 4) = local_40._4_4_;
      }
      local_24 = 0.0;
      local_1c = *(undefined4 *)(pdVar5 + 100);
      uStack_18 = *(undefined4 *)((int)pdVar5 + 0x324);
      for (local_8 = 0x65; local_8 < 1000; local_8 = local_8 + 1) {
        uVar3 = *(undefined4 *)(pdVar5 + local_8);
        uVar4 = *(undefined4 *)((int)pdVar5 + local_8 * 8 + 4);
        pdVar5[local_8] =
             (double)CONCAT44(uVar4,uVar3) / _DAT_10038a38 +
             ((double)CONCAT44(uStack_18,local_1c) + pdVar5[local_8 + 1]) / _DAT_10038a30;
        if (local_24 < pdVar5[local_8]) {
          local_24 = ((_DAT_10038a18 - _DAT_10038a28) * local_24 + pdVar5[local_8]) / _DAT_10038a18;
        }
        local_1c = uVar3;
        uStack_18 = uVar4;
      }
      local_24 = local_24 / _DAT_10038a38;
      local_28 = 1;
      for (local_8 = 100; local_8 < 1000; local_8 = local_8 + 1) {
        if ((local_24 < pdVar5[local_8]) &&
           (pdVar5[local_8 + -1] < pdVar5[local_8] && pdVar5[local_8 + 1] < pdVar5[local_8])) {
          local_28 = local_8 - local_28;
          if ((2 < local_28) && (local_28 < *(int *)(this + 0x1b0) + -1)) {
            param_1[local_14 + -1] = param_1[local_14 + -1] + local_28;
            param_2[local_14 + -1] = param_2[local_14 + -1] + 1;
          }
          local_28 = local_8;
        }
      }
    }
    free_dvector(pdVar5,1,1000);
  }
  return;
}

//===== 0x100186bc =====

void FUN_100186bc(void)

{
  FUN_100186c6();
  return;
}

//===== 0x100186c6 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_100186c6(void)

{
  _DAT_10041f78 = acos(-1.0);
  return;
}

//===== 0x100186e0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

float10 FUN_100186e0(void)

{
  int iVar1;
  
  iVar1 = rand();
  return (float10)iVar1 / (float10)_DAT_10038a48;
}

//===== 0x100186fa =====

void __cdecl FUN_100186fa(int param_1,int param_2,int param_3)

{
  float10 fVar1;
  undefined4 local_c;
  undefined4 local_8;
  
  for (local_8 = 1; local_8 <= param_2; local_8 = local_8 + 1) {
    for (local_c = 1; local_c <= param_3; local_c = local_c + 1) {
      fVar1 = FUN_100186e0();
      *(double *)(*(int *)(param_1 + local_8 * 4) + local_c * 8) = (double)fVar1;
    }
  }
  return;
}

//===== 0x10018750 =====

undefined4 __cdecl FUN_10018750(double *param_1,double *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x1001879e =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: int __thiscall Wvfm::nreader(int,int,class SegRead &,int,struct TestOptions const &) */

int __thiscall
Wvfm::nreader(Wvfm *this,int param_1,int param_2,SegRead *param_3,int param_4,TestOptions *param_5)

{
  int iVar1;
  short sVar2;
  Wvfm *pWVar3;
  Method MVar4;
  DATASRC DVar5;
  char *pcVar6;
  int iVar7;
  ShftVect *pSVar8;
  double *pdVar9;
  double dVar10;
  size_t sVar11;
  uint uVar12;
  Wvfm *local_128;
  Wvfm *local_118;
  Wvfm *local_10c;
  Mobility local_bc [24];
  int local_a4;
  short local_a0;
  double local_9c;
  double local_94;
  double local_8c;
  double local_84;
  double local_7c;
  int local_74;
  int local_70;
  double *local_6c;
  int local_68;
  int *local_64;
  int local_60;
  double **local_5c;
  int local_58;
  int local_54;
  int **local_50;
  ShftVect local_4c [8];
  size_t local_44;
  int local_40;
  int local_3c;
  Wvfm *local_38;
  int local_34;
  Wvfm *local_30;
  Wvfm *local_2c;
  Wvfm *local_28;
  int local_24;
  Wvfm *local_20;
  int local_1c;
  Wvfm *local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x1879e  286  ?nreader@Wvfm@@AAEHHHAAVSegRead@@HABUTestOptions@@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037056;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  local_14 = Annotate::getNumCurrFix((Annotate *)param_3);
  pWVar3 = operator_new(0x308);
  local_8 = 0;
  if (pWVar3 == (Wvfm *)0x0) {
    local_10c = (Wvfm *)0x0;
  }
  else {
    MVar4 = method(this);
    DVar5 = ds(this);
    pcVar6 = lnordr(this);
    local_10c = (Wvfm *)Wvfm(pWVar3,0x800,4,pcVar6,DVar5,MVar4);
  }
  local_8 = 0xffffffff;
  local_18 = local_10c;
  local_50 = (int **)0x0;
  if (local_10c == (Wvfm *)0x0) {
    local_3c = 0;
  }
  else {
    local_28 = local_10c;
    *(undefined4 *)(local_10c + 0x1b0) = *(undefined4 *)(this + 0x1b0);
    local_1c = endi(this);
    local_34 = local_14 + 0x7ff;
    if (local_1c < local_34) {
      local_5c = (double **)0x0;
      local_6c = (double *)0x0;
      local_60 = local_34 - local_1c;
      local_74 = 1;
      local_64 = &local_74;
      local_70 = 1;
      local_5c = dmatrix(1,local_60 + 10,1,1);
      if (local_5c == (double **)0x0) {
        *(undefined4 *)(this + 0x168) = 2;
        ExceptionList = local_10;
        return 0;
      }
      FUN_100186fa((int)local_5c,local_60 + 10,local_70);
      local_44 = (local_1c - local_14) + 1;
      local_58 = ftol();
      local_68 = local_44 - local_58;
      local_6c = dvector(1,local_44);
      for (local_40 = 1; local_40 <= (int)local_44; local_40 = local_40 + 1) {
        *(undefined4 *)(*(int *)(local_28 + 0x300) + local_40 * 4) =
             *(undefined4 *)(*(int *)(this + 0x300) + -4 + (local_14 + local_40) * 4);
      }
      for (local_54 = 1; local_54 < 5; local_54 = local_54 + 1) {
        for (local_40 = 1; local_40 <= (int)local_44; local_40 = local_40 + 1) {
          dVar10 = sc_la(this,local_14 + -1 + local_40,local_54);
          local_6c[local_40] = dVar10;
          sc_la_set(local_28,local_40,local_54,
                    (double)CONCAT44(*(undefined4 *)((int)local_6c + local_40 * 8 + 4),
                                     *(undefined4 *)(local_6c + local_40)));
        }
        qsort(local_6c + 1,local_44,8,FUN_10018750);
        local_7c = local_6c[local_68] - local_6c[local_58];
        for (local_40 = 1; local_40 < 0xb; local_40 = local_40 + 1) {
          local_8c = sc_la(local_28,local_44 - (10 - local_40),local_54);
          local_84 = local_7c * local_5c[local_40][*local_64];
          dVar10 = cos(((double)local_40 * _DAT_10041fe0) / _DAT_10038a60);
          local_94 = (dVar10 + _DAT_10038a68) * _DAT_10038a58;
          dVar10 = cos(((double)local_40 * _DAT_10041fe0) / _DAT_10038a60 + _DAT_10041fe0);
          local_9c = (dVar10 + _DAT_10038a68) * _DAT_10038a58;
          sc_la_set(local_28,local_40,local_54,local_9c * local_84 + local_94 * local_8c);
        }
        for (local_40 = 1; local_40 <= local_60; local_40 = local_40 + 1) {
          sc_la_set(local_28,local_44 + local_40,local_54,
                    local_7c * local_5c[local_40 + 10][*local_64]);
        }
      }
      free_dmatrix(local_5c,1,local_60 + 10,1,local_70);
      free_dvector(local_6c,1,local_44);
    }
    else {
      local_44 = 0x800;
      local_24 = 1;
      for (local_40 = local_14; local_40 <= local_34; local_40 = local_40 + 1) {
        *(undefined4 *)(*(int *)(local_28 + 0x300) + local_24 * 4) =
             *(undefined4 *)(*(int *)(this + 0x300) + local_40 * 4);
        for (local_54 = 1; local_54 < 5; local_54 = local_54 + 1) {
          iVar7 = *(int *)(*(int *)(this + 0xc4) + local_40 * 4);
          iVar1 = *(int *)(*(int *)(local_28 + 0xc4) + local_24 * 4);
          *(undefined4 *)(iVar1 + local_54 * 8) = *(undefined4 *)(iVar7 + local_54 * 8);
          *(undefined4 *)(iVar1 + 4 + local_54 * 8) = *(undefined4 *)(iVar7 + 4 + local_54 * 8);
        }
        local_24 = local_24 + 1;
      }
    }
    pWVar3 = operator_new(0x308);
    local_8 = 1;
    if (pWVar3 == (Wvfm *)0x0) {
      local_118 = (Wvfm *)0x0;
    }
    else {
      local_118 = (Wvfm *)Wvfm(pWVar3,local_28);
    }
    local_8 = 0xffffffff;
    local_30 = local_118;
    if (local_118 == (Wvfm *)0x0) {
      if (local_18 != (Wvfm *)0x0) {
        FUN_10019250(local_18,1);
      }
      local_3c = 0;
    }
    else {
      local_2c = local_118;
      FUN_1000b7a0(param_3,local_28,param_1,(uint *)param_5);
      iVar7 = FUN_10033324(param_3,local_28,local_2c,local_44,param_2,(uint *)param_5);
      if (iVar7 == 1) {
        pWVar3 = operator_new(0x308);
        local_8 = 2;
        if (pWVar3 == (Wvfm *)0x0) {
          local_128 = (Wvfm *)0x0;
        }
        else {
          MVar4 = method(this);
          DVar5 = ds(this);
          pcVar6 = lnordr(this);
          iVar7 = 4;
          pSVar8 = (ShftVect *)FUN_100241e0((int)param_3);
          sVar2 = ShftVect::maxshft(pSVar8);
          local_128 = (Wvfm *)Wvfm(pWVar3,sVar2 + 0x800,iVar7,pcVar6,DVar5,MVar4);
        }
        local_8 = 0xffffffff;
        local_20 = local_128;
        local_38 = local_128;
        iVar7 = 0;
        pdVar9 = ssm(this);
        ssm(local_38,pdVar9,iVar7);
        *(undefined4 *)(local_38 + 0x1b0) = *(undefined4 *)(this + 0x1b0);
        for (local_54 = 1; local_54 < 5; local_54 = local_54 + 1) {
          iVar7 = local_54;
          pSVar8 = (ShftVect *)FUN_100241e0((int)param_3);
          local_a0 = ShftVect::s(pSVar8,iVar7);
          local_24 = (int)local_a0;
          for (local_40 = 1; local_24 = local_24 + 1, local_40 < 0x801; local_40 = local_40 + 1) {
            iVar7 = *(int *)(*(int *)(local_28 + 0xc4) + local_40 * 4);
            iVar1 = *(int *)(*(int *)(local_38 + 0xc4) + local_24 * 4);
            *(undefined4 *)(iVar1 + local_54 * 8) = *(undefined4 *)(iVar7 + local_54 * 8);
            *(undefined4 *)(iVar1 + 4 + local_54 * 8) = *(undefined4 *)(iVar7 + 4 + local_54 * 8);
          }
        }
        for (local_40 = 1; local_40 < 0x801; local_40 = local_40 + 1) {
          *(undefined4 *)(*(int *)(local_38 + 0x300) + local_40 * 4) =
               *(undefined4 *)(*(int *)(local_28 + 0x300) + local_40 * 4);
        }
        for (; local_40 <= *(int *)(local_38 + 0xb0); local_40 = local_40 + 1) {
          *(undefined4 *)(*(int *)(local_38 + 0x300) + local_40 * 4) =
               *(undefined4 *)(*(int *)(local_28 + 0x300) + 0x2000);
        }
        if ((param_2 & 2U) != 0) {
          pSVar8 = (ShftVect *)FUN_100241e0((int)param_3);
          sVar2 = ShftVect::maxshft(pSVar8);
          endi(local_38,local_44 + (int)sVar2);
        }
        if (param_4 == 1) {
          local_a4 = bgni(local_38);
          pSVar8 = (ShftVect *)FUN_100241e0((int)param_3);
          sVar2 = ShftVect::maxshft(pSVar8);
          bgni(local_38,sVar2 + 1);
          Mobility::Mobility(local_bc,local_38,0x2ee);
          local_8 = 3;
          Mobility::search(local_bc);
          if ((param_2 & 2U) != 0) {
            local_50 = imatrix(1,4,1,0x2ee);
          }
          Mobility::apply(local_bc,local_50);
          bgni(local_38,local_a4);
          local_8 = 0xffffffff;
          Mobility::~Mobility(local_bc);
        }
        FUN_10024d90(param_3,local_38);
        ShftVect::ShftVect(local_4c);
        pSVar8 = local_4c;
        pWVar3 = (Wvfm *)SW::alignedLength((SW *)param_3);
        envelope(pWVar3,pSVar8);
        sVar11 = local_44;
        uVar12 = param_2;
        pcVar6 = lnordr(this);
        local_3c = FUN_10019ef2(param_3,(int)pcVar6,param_1,sVar11,uVar12,param_4,(uint *)param_5);
        if ((local_3c == 1) && ((param_2 & 2U) != 0)) {
          FUN_10026435(param_3,local_2c,0x2ee,(int)local_50);
        }
        if (local_50 != (int **)0x0) {
          free_imatrix(local_50,1,4,1,0x2ee);
        }
        if ((local_18 != (Wvfm *)0x0) && (local_18 != (Wvfm *)0x0)) {
          FUN_10019250(local_18,1);
        }
        if ((local_30 != (Wvfm *)0x0) && (local_30 != (Wvfm *)0x0)) {
          FUN_10019250(local_30,1);
        }
        if ((local_20 != (Wvfm *)0x0) && (local_20 != (Wvfm *)0x0)) {
          FUN_10019250(local_20,1);
        }
      }
      else {
        if (local_18 != (Wvfm *)0x0) {
          FUN_10019250(local_18,1);
        }
        if (local_30 != (Wvfm *)0x0) {
          FUN_10019250(local_30,1);
        }
        local_3c = 0;
      }
    }
  }
  ExceptionList = local_10;
  return local_3c;
}

//===== 0x10019225 =====

void FUN_10019225(void)

{
  FUN_1001922f();
  return;
}

//===== 0x1001922f =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1001922f(void)

{
  _DAT_10041fe0 = acos(-1.0);
  return;
}

//===== 0x10019250 =====

Wvfm * __thiscall FUN_10019250(void *this,uint param_1)

{
  Wvfm::~Wvfm(this);
  if ((param_1 & 1) != 0) {
    operator_delete(this);
  }
  return this;
}

//===== 0x10019280 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __cdecl FUN_10019280(int param_1,int param_2,int *param_3,int param_4)

{
  bool bVar1;
  undefined4 uVar2;
  int *piVar3;
  int iVar4;
  double dVar5;
  double dVar6;
  int local_74;
  double local_54;
  int local_4c;
  int local_48;
  int local_44;
  double local_40;
  double local_30;
  float local_28 [2];
  float local_20;
  float local_1c;
  int local_18;
  int local_10;
  double local_c;
  
  if (param_4 < 4) {
    uVar2 = 0;
  }
  else {
    piVar3 = ivector(1,param_4);
    if (piVar3 == (int *)0x0) {
      uVar2 = 0;
    }
    else {
      local_54 = 0.0;
      local_30 = 0.0;
      local_c = 0.0;
      local_40 = 0.0;
      for (local_4c = 1; local_4c <= param_4; local_4c = local_4c + 1) {
        dVar5 = (double)*(int *)(param_2 + local_4c * 4);
        local_54 = local_54 + dVar5;
        local_30 = dVar5 * dVar5 + local_30;
      }
      local_54 = local_54 / (double)param_4;
      dVar5 = sqrt(local_30 / (double)param_4 - local_54 * local_54);
      local_48 = 0;
      if (_DAT_10038a98 == (float)dVar5) {
        free_ivector(piVar3,1,param_4);
        uVar2 = 0;
      }
      else {
        for (local_4c = 1; local_4c <= param_4; local_4c = local_4c + 1) {
          dVar6 = fabs(((double)*(int *)(param_2 + local_4c * 4) - local_54) / (double)(float)dVar5)
          ;
          if (dVar6 <= _DAT_10038aa0) {
            local_48 = local_48 + 1;
            piVar3[local_48] = *(int *)(param_1 + local_4c * 4);
            param_3[local_48] = *(int *)(param_2 + local_4c * 4);
            local_c = (double)param_3[local_48] + local_c;
            local_40 = (double)(param_3[local_48] * param_3[local_48]) + local_40;
          }
        }
        local_c = local_c / (double)local_48;
        sqrt(local_40 / (double)local_48 - local_c * local_c);
        iVar4 = iquadratic(piVar3,param_3,local_48,local_28);
        if (iVar4 == 1) {
          dVar5 = sqrt((double)local_1c);
          local_18 = 1;
          for (local_10 = 1; local_10 <= param_4; local_10 = local_10 + 1) {
            iVar4 = ftol();
            param_3[local_18] = iVar4;
            piVar3[local_18] = *(int *)(param_1 + local_10 * 4);
            iVar4 = abs(param_3[local_18] - *(int *)(param_2 + local_10 * 4));
            if ((float)iVar4 < (float)dVar5) {
              local_18 = local_18 + 1;
            }
          }
          local_18 = local_18 + -1;
          if (3 < local_18) {
            iVar4 = iquadratic(piVar3,param_3,local_18,local_28);
            if (iVar4 != 1) {
              free_ivector(piVar3,1,param_4);
              return 0;
            }
            for (local_10 = 1; local_10 <= param_4; local_10 = local_10 + 1) {
              iVar4 = ftol();
              param_3[local_10] = iVar4;
            }
          }
          free_ivector(piVar3,1,param_4);
          if (((_DAT_10038a98 != local_20) && (iVar4 = ftol(), *(int *)(param_1 + 4) <= iVar4)) &&
             (iVar4 <= *(int *)(param_1 + param_4 * 4))) {
            for (local_74 = 1; *(int *)(param_1 + local_74 * 4) < iVar4; local_74 = local_74 + 1) {
            }
            iVar4 = param_3[local_74];
            local_10 = local_74;
            if (local_20 <= (float)_DAT_10038ab8) {
              while (local_10 = local_10 + 1, local_10 <= param_4) {
                param_3[local_10] = iVar4;
              }
            }
            else {
              for (local_10 = 1; local_10 < local_74; local_10 = local_10 + 1) {
                param_3[local_10] = iVar4;
              }
            }
          }
          local_44 = 1000000;
          bVar1 = false;
          for (local_10 = 1; local_10 <= param_4; local_10 = local_10 + 1) {
            if (param_3[local_10] < 1) {
              bVar1 = true;
            }
            else if (param_3[local_10] < local_44) {
              local_44 = param_3[local_10];
            }
          }
          if (bVar1) {
            if (local_44 < 1) {
              local_44 = 1;
            }
            for (local_10 = 1; local_10 <= param_4; local_10 = local_10 + 1) {
              if (param_3[local_10] < local_44) {
                param_3[local_10] = local_44;
              }
            }
          }
          uVar2 = 1;
        }
        else {
          free_ivector(piVar3,1,param_4);
          uVar2 = 0;
        }
      }
    }
  }
  return uVar2;
}

//===== 0x100197cf =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int __thiscall FUN_100197cf(void *this,uint param_1,int param_2)

{
  Wvfm *this_00;
  int iVar1;
  int iVar2;
  double dVar3;
  double dVar4;
  undefined8 local_30;
  undefined4 local_28;
  undefined8 local_1c;
  undefined4 local_14;
  undefined8 local_10;
  undefined4 local_8;
  
  this_00 = (Wvfm *)SW::alignedLength(this);
  local_10 = 0.0;
  local_1c = 0.0;
  local_14 = param_1;
  iVar2 = (param_2 - param_1) + 1;
  if (iVar2 < 2) {
    iVar1 = iVar2 / 2 + param_1;
  }
  else {
    local_30 = 100000.0;
    for (local_28 = param_1; local_8 = param_1, (int)local_28 <= param_2; local_28 = local_28 + 1) {
      dVar3 = Wvfm::envv(this_00,local_28);
      if (dVar3 < local_30) {
        local_30 = Wvfm::envv(this_00,local_28);
      }
    }
    while (local_8 = local_8 + 1, (int)local_8 <= param_2) {
      dVar3 = Wvfm::envv(this_00,local_14);
      dVar4 = Wvfm::envv(this_00,local_8);
      local_10 = ((double)(int)local_8 * _DAT_10038ab0 + (double)(int)local_14) * (dVar4 - local_30)
                 + ((double)(int)local_14 * _DAT_10038ab0 + (double)(int)local_8) *
                   (dVar3 - local_30) + local_10;
      local_1c = (dVar3 - local_30) + (dVar4 - local_30) + local_1c;
      local_14 = local_14 + 1;
    }
    if (_DAT_10038ab8 == local_1c) {
      iVar1 = iVar2 / 2 + param_1;
    }
    else {
      if (local_10 / (_DAT_10038ac8 * local_1c) <= _DAT_10038ab8) {
        dVar3 = local_10 / (_DAT_10038ac8 * local_1c) - _DAT_10038ac0;
      }
      else {
        dVar3 = local_10 / (_DAT_10038ac8 * local_1c) + _DAT_10038ac0;
      }
      iVar1 = ftol(dVar3);
      if ((iVar1 < (int)param_1) || (param_2 < iVar1)) {
        iVar1 = param_1 + iVar2 / 2;
      }
    }
  }
  return iVar1;
}

//===== 0x10019991 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __thiscall FUN_10019991(void *this,int param_1,int *param_2,int param_3,int param_4)

{
  int iVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  double dVar4;
  double dVar5;
  int local_a0;
  int local_84;
  int local_7c;
  int local_78;
  undefined4 local_74;
  undefined4 uStack_70;
  int local_6c;
  int aiStack_68 [5];
  undefined4 local_54;
  undefined4 uStack_50;
  int local_4c;
  int local_48;
  int local_44;
  undefined8 local_40;
  int local_38;
  undefined8 uStack_34;
  Wvfm *local_c;
  int local_8;
  
  local_c = *(Wvfm **)((int)this + 8);
  local_8 = 1;
  do {
    if (*param_2 < local_8) {
      return 0;
    }
    iVar1 = Wvfm::annotate((Wvfm *)((int)this + local_8 * 0x14 + 0x1c));
    if ((param_3 < iVar1) &&
       (iVar1 = SW::alignedLength((SW *)((int)this + local_8 * 0x14 + 0x1c)), iVar1 < param_4)) {
      local_44 = Wvfm::annotate((Wvfm *)((int)this + local_8 * 0x14 + 0x1c));
      local_4c = SW::alignedLength((SW *)((int)this + local_8 * 0x14 + 0x1c));
      local_38 = Annotate::getNumCurrFix((Annotate *)((int)this + local_8 * 0x14 + 0x1c));
      local_48 = 1;
      local_40 = Wvfm::sc_la(local_c,local_38,1);
      for (local_6c = 2; local_6c < 5; local_6c = local_6c + 1) {
        dVar4 = Wvfm::sc_la(local_c,local_38,local_6c);
        if (local_40 < dVar4) {
          local_48 = local_6c;
          local_40 = Wvfm::sc_la(local_c,local_38,local_6c);
        }
      }
      local_40 = 0.0;
      for (local_6c = 1; local_6c < 5; local_6c = local_6c + 1) {
        local_54 = 0;
        uStack_50 = 0;
        aiStack_68[local_6c] = local_44;
        *(undefined4 *)(&uStack_34 + local_6c) = 0;
        *(undefined4 *)((int)&uStack_34 + local_6c * 8 + 4) = 0;
        for (local_38 = local_44; local_38 <= local_4c; local_38 = local_38 + 1) {
          dVar4 = Wvfm::sc_la(local_c,local_38,local_6c);
          if ((_DAT_10038ab8 < dVar4) &&
             ((&uStack_34)[local_6c] = (double)(&uStack_34)[local_6c] + dVar4,
             (double)CONCAT44(uStack_50,local_54) < dVar4)) {
            local_74 = SUB84(dVar4,0);
            local_54 = local_74;
            uStack_70 = (undefined4)((ulonglong)dVar4 >> 0x20);
            uStack_50 = uStack_70;
            aiStack_68[local_6c] = local_38;
          }
        }
        if (local_40 < (double)(&uStack_34)[local_6c]) {
          local_40 = (double)CONCAT44(local_40._4_4_,*(undefined4 *)(&uStack_34 + local_6c));
          local_40 = (double)CONCAT44(*(undefined4 *)((int)&uStack_34 + local_6c * 8 + 4),
                                      *(undefined4 *)(&uStack_34 + local_6c));
        }
      }
      if (_DAT_10038ab8 != local_40) {
        local_78 = 0;
        local_7c = 0;
        for (local_6c = 1; local_6c < 5; local_6c = local_6c + 1) {
          (&uStack_34)[local_6c] = (double)(&uStack_34)[local_6c] / local_40;
          iVar1 = aiStack_68[local_6c];
          if ((((local_48 != local_6c) && ((double)(&uStack_34)[local_6c] < _DAT_10038ad0)) &&
              (_DAT_10038a78 < (double)(&uStack_34)[local_6c])) &&
             ((iVar1 != local_44 && (iVar1 != local_4c)))) {
            dVar4 = Wvfm::sc_la(local_c,iVar1 + -1,local_6c);
            dVar5 = Wvfm::sc_la(local_c,iVar1,local_6c);
            if (dVar4 < dVar5) {
              dVar4 = Wvfm::sc_la(local_c,iVar1,local_6c);
              dVar5 = Wvfm::sc_la(local_c,iVar1 + 1,local_6c);
              if (dVar5 < dVar4) {
                local_78 = local_78 + 1;
                local_7c = local_6c;
              }
            }
          }
        }
        if (local_78 == 1) {
          iVar1 = Annotate::getNumCurrFix((Annotate *)((int)this + local_8 * 0x14 + 0x1c));
          if (aiStack_68[local_7c] < iVar1) {
            local_a0 = local_8;
          }
          else {
            local_a0 = local_8 + 1;
          }
          for (local_84 = *param_2 + 1; local_a0 < local_84; local_84 = local_84 + -1) {
            puVar2 = (undefined4 *)((int)this + (local_84 + -1) * 0x14 + 0x1c);
            puVar3 = (undefined4 *)((int)this + local_84 * 0x14 + 0x1c);
            for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
              *puVar3 = *puVar2;
              puVar2 = puVar2 + 1;
              puVar3 = puVar3 + 1;
            }
            *(undefined1 *)((int)this + local_84 + 0xa01c) =
                 *(undefined1 *)((int)this + local_84 + 0xa01b);
          }
          RdrOut::iS1((RdrOut *)((int)this + local_a0 * 0x14 + 0x1c),aiStack_68[local_7c]);
          iVar1 = aiStack_68[local_7c];
          do {
            local_84 = iVar1 + -1;
            if (local_84 <= local_44) break;
            dVar4 = Wvfm::sc_la(local_c,local_84,local_7c);
            dVar5 = Wvfm::sc_la(local_c,iVar1,local_7c);
            iVar1 = local_84;
          } while (dVar4 < dVar5);
          Wvfm::annotate((Wvfm *)((int)this + local_a0 * 0x14 + 0x1c),local_84);
          iVar1 = aiStack_68[local_7c];
          do {
            local_84 = iVar1 + 1;
            if (local_4c <= local_84) break;
            dVar4 = Wvfm::sc_la(local_c,local_84,local_7c);
            dVar5 = Wvfm::sc_la(local_c,iVar1,local_7c);
            iVar1 = local_84;
          } while (dVar4 < dVar5);
          BandStat::bbgn((BandStat *)((int)this + local_a0 * 0x14 + 0x1c),local_84);
          BandStat::insr((BandStat *)((int)this + local_a0 * 0x14 + 0x1c),1);
          *(undefined1 *)((int)this + local_a0 + 0xa01c) = *(undefined1 *)(param_1 + local_7c + -1);
          local_8 = local_8 + 1;
          *param_2 = *param_2 + 1;
        }
      }
    }
    local_8 = local_8 + 1;
  } while( true );
}

//===== 0x10019ef2 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __thiscall
FUN_10019ef2(void *this,int param_1,int param_2,int param_3,uint param_4,int param_5,uint *param_6)

{
  int iVar1;
  uint uVar2;
  undefined4 *puVar3;
  int *piVar4;
  int iVar5;
  undefined4 uVar6;
  float **ppfVar7;
  int iVar8;
  BandStat *pBVar9;
  undefined4 *puVar10;
  double dVar11;
  double dVar12;
  float *pfVar13;
  float local_230;
  float local_200;
  BandStat local_1ec [20];
  undefined4 local_1d8;
  undefined4 local_1d4;
  undefined4 local_1d0;
  undefined4 local_1cc;
  undefined4 local_1c8;
  undefined4 local_1c4;
  undefined4 local_1c0;
  undefined4 local_1bc;
  BandStat local_1b8 [20];
  undefined4 local_1a4;
  undefined4 local_1a0;
  undefined4 local_19c;
  BandStat local_198 [20];
  undefined4 local_184;
  undefined4 local_180;
  undefined4 local_17c;
  undefined4 local_178;
  undefined4 local_174;
  undefined4 local_170;
  BandStat local_16c [20];
  undefined4 local_158;
  undefined4 local_154;
  undefined4 local_150;
  undefined4 local_14c;
  undefined4 local_148;
  undefined4 local_144;
  undefined4 local_140;
  undefined4 local_13c;
  BandStat local_138 [20];
  undefined4 local_124;
  int local_120;
  float local_11c;
  float local_118;
  int local_114;
  int local_110;
  BandStat local_10c [20];
  uint local_f8;
  int local_f4;
  int local_f0;
  double local_ec;
  float local_e4;
  float local_e0;
  int local_dc;
  float local_d8;
  float local_d4;
  int local_d0;
  int local_cc;
  int local_c8;
  double local_c4;
  int local_bc;
  int local_b8;
  int local_b4;
  int local_b0;
  int local_ac;
  int local_a8;
  Annotate *local_a4;
  int local_a0;
  int local_9c;
  int local_98;
  int local_94;
  float **local_90;
  int local_8c;
  CCmdUI local_88 [40];
  CCmdUI local_60 [40];
  float *local_38;
  float *local_34;
  int *local_30;
  float *local_2c;
  int *local_28;
  int *local_24;
  uint local_20;
  int local_1c;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  int local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037081;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  CCmdUI::CCmdUI(local_88);
  local_8 = 0;
  CCmdUI::CCmdUI(local_60);
  local_8._0_1_ = 1;
  local_34 = (float *)0x0;
  local_38 = (float *)0x0;
  local_2c = (float *)0x0;
  local_90 = (float **)0x0;
  local_28 = (int *)0x0;
  local_24 = (int *)0x0;
  local_30 = (int *)0x0;
  local_8c = 0;
  iVar1 = FUN_1002511d(this,param_3,local_88);
  if (iVar1 == 1) {
    if ((*param_6 >> 3 & 1) != 0) {
      local_98 = 0;
      local_9c = 0;
      local_a8 = 0;
      local_a4 = (Annotate *)local_88;
      local_b8 = 1;
      local_b4 = Annotate::getCFlen(local_a4);
      local_b0 = local_b4;
      for (local_ac = 1; local_ac <= local_b0; local_ac = local_ac + 1) {
        uVar2 = FUN_1001bb80(local_a4,local_ac);
        local_c4 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
        if (local_a8 == 0) {
          if (local_c4 <= _DAT_10038a88) {
            if (0 < local_9c) {
              local_9c = local_9c + -1;
            }
          }
          else {
            local_9c = local_9c + 1;
            if (10 < local_9c) {
              local_a8 = 1;
              local_94 = (local_ac - local_9c) + 1;
              local_a0 = local_ac;
              local_9c = 0;
            }
          }
        }
        else {
          local_a0 = local_ac;
          if (_DAT_10038a88 < local_c4) {
            if (0 < local_9c) {
              local_9c = local_9c + -1;
            }
          }
          else {
            local_9c = local_9c + 1;
            if (10 < local_9c) {
              local_a8 = 0;
              local_a0 = local_ac - local_9c;
              local_9c = 0;
              if (local_98 < local_a0 - local_94) {
                local_98 = local_a0 - local_94;
                local_b8 = local_94;
                local_b4 = local_a0;
              }
            }
          }
        }
      }
      if ((local_a8 == 1) && (local_a0 = local_a0 - local_9c, local_98 < local_a0 - local_94)) {
        local_b8 = local_94;
        local_b4 = local_a0;
      }
      local_bc = 0;
      for (local_ac = 1; local_ac <= local_b4; local_ac = local_ac + 1) {
        uVar2 = FUN_1001bb80(local_a4,local_ac);
        dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
        if (_DAT_10038a88 < dVar11) {
          puVar3 = FUN_1001bbe0(local_a4,(undefined4 *)local_138,local_ac);
          local_bc = local_bc + 1;
          puVar10 = (undefined4 *)((int)this + local_bc * 0x14 + 0x1c);
          for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
            *puVar10 = *puVar3;
            puVar3 = puVar3 + 1;
            puVar10 = puVar10 + 1;
          }
          BandStat::~BandStat(local_138);
        }
      }
      FUN_1001e34e(local_a4,(int)this + 0x1c,local_bc);
    }
    local_20 = Annotate::getCFlen((Annotate *)local_88);
    if ((int)local_20 < 0x800) {
      piVar4 = ivector(1,local_20);
      local_24 = piVar4;
      if (piVar4 == (int *)0x0) {
        *(undefined4 *)this = 2;
        local_140 = 0;
        local_8 = (uint)local_8._1_3_ << 8;
        FUN_1001dece((int)local_60);
        local_8 = 0xffffffff;
        FUN_1001dece((int)local_88);
        uVar6 = local_140;
      }
      else {
        uVar2 = local_20;
        iVar1 = SSNODE::SWold((SSNODE *)local_88);
        iVar5 = Annotate::getNumCurrFix((Annotate *)local_88);
        iVar1 = FUN_10019280(iVar5,iVar1,piVar4,uVar2);
        if (iVar1 == 1) {
          local_34 = FUN_10024e47(this,(Annotate *)local_88);
          if (local_34 == (float *)0x0) {
            free_ivector(local_24,1,local_20);
            *(undefined4 *)this = 2;
            local_148 = 0;
            local_8 = (uint)local_8._1_3_ << 8;
            FUN_1001dece((int)local_60);
            local_8 = 0xffffffff;
            FUN_1001dece((int)local_88);
            uVar6 = local_148;
          }
          else {
            iVar1 = Wvfm::rows(*(Wvfm **)((int)this + 8));
            local_28 = ivector(1,iVar1);
            if (local_28 == (int *)0x0) {
              *(undefined4 *)this = 2;
              free_ivector(local_24,1,local_20);
              free_vector(local_34,1,local_20);
              local_14c = 0;
              local_8 = (uint)local_8._1_3_ << 8;
              FUN_1001dece((int)local_60);
              local_8 = 0xffffffff;
              FUN_1001dece((int)local_88);
              uVar6 = local_14c;
            }
            else {
              FUN_10025431(this,param_3,(int)local_28);
              if (local_8c != 0) {
                local_d0 = Annotate::getNumCurrFix((Annotate *)local_88);
                local_c8 = SSNODE::SWold((SSNODE *)local_88);
                for (local_cc = 1; local_cc <= (int)local_20; local_cc = local_cc + 1) {
                  iVar1 = local_24[local_cc];
                  dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),*(uint *)(local_d0 + local_cc * 4));
                  printf(s__d__d___3f__d_1003fc10,*(undefined4 *)(local_d0 + local_cc * 4),
                         *(undefined4 *)(local_c8 + local_cc * 4),SUB84(dVar11,0),
                         (int)((ulonglong)dVar11 >> 0x20),iVar1);
                }
                local_8c = 0;
              }
              local_38 = vector(1,local_20);
              if (local_38 == (float *)0x0) {
                *(undefined4 *)this = 2;
                free_ivector(local_24,1,local_20);
                free_vector(local_34,1,local_20);
                iVar1 = Wvfm::rows(*(Wvfm **)((int)this + 8));
                free_ivector(local_28,1,iVar1);
                local_150 = 0;
                local_8 = (uint)local_8._1_3_ << 8;
                FUN_1001dece((int)local_60);
                local_8 = 0xffffffff;
                FUN_1001dece((int)local_88);
                uVar6 = local_150;
              }
              else {
                for (local_14 = 1; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                  uVar2 = FUN_1001bb80(local_88,local_14);
                  dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
                  local_38[local_14] = (float)dVar11;
                }
                local_2c = vector(1,local_20);
                if (local_2c == (float *)0x0) {
                  *(undefined4 *)this = 2;
                  free_ivector(local_24,1,local_20);
                  free_vector(local_34,1,local_20);
                  iVar1 = Wvfm::rows(*(Wvfm **)((int)this + 8));
                  free_ivector(local_28,1,iVar1);
                  free_vector(local_38,1,local_20);
                  local_154 = 0;
                  local_8 = (uint)local_8._1_3_ << 8;
                  FUN_1001dece((int)local_60);
                  local_8 = 0xffffffff;
                  FUN_1001dece((int)local_88);
                  uVar6 = local_154;
                }
                else {
                  for (local_14 = 1; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                    uVar2 = FUN_1001bb60(local_88,local_14);
                    dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
                    local_d4 = (float)dVar11;
                    uVar2 = FUN_1001bba0(local_88,local_14);
                    dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
                    local_d8 = (float)dVar11;
                    local_200 = local_d8;
                    if (local_d4 < local_d8) {
                      local_200 = local_d4;
                    }
                    local_2c[local_14] = local_200;
                  }
                  if (local_8c != 0) {
                    for (local_14 = 1; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                      dVar11 = (double)local_38[local_14];
                      dVar12 = (double)local_2c[local_14];
                      iVar1 = FUN_1001bb80(local_88,local_14);
                      iVar1 = (int)"?ACTG"[local_28[iVar1]];
                      uVar6 = FUN_1001bb80(local_88,local_14);
                      printf(s__3d__4d__c__5_3f__5_3f_1003fc20,local_14,uVar6,iVar1,SUB84(dVar12,0),
                             (int)((ulonglong)dVar12 >> 0x20),SUB84(dVar11,0),
                             (int)((ulonglong)dVar11 >> 0x20));
                    }
                    printf(s_omitokn__1__peaks_1003fc38);
                    FUN_1001e8a8((int)local_88);
                  }
                  ppfVar7 = matrix(1,local_20,1,2);
                  pfVar13 = local_34;
                  uVar2 = local_20;
                  local_90 = ppfVar7;
                  iVar1 = FUN_1001bcd0((int)local_88);
                  iVar5 = SSNODE::SWold((SSNODE *)local_88);
                  local_1c = FUN_10012140((int)local_24,local_38,(int)local_2c,iVar5,iVar1,pfVar13,
                                          uVar2,(int)ppfVar7);
                  free_vector(local_38,1,local_20);
                  local_38 = (float *)0x0;
                  free_vector(local_2c,1,local_20);
                  local_2c = (float *)0x0;
                  free_ivector(local_24,1,local_20);
                  local_24 = (int *)0x0;
                  if (local_1c == 1) {
                    local_18 = 1;
                    for (local_14 = 1; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                      iVar1 = ftol();
                      if (iVar1 == 1) {
LAB_1001aab0:
                        puVar3 = FUN_1001bbe0(local_88,(undefined4 *)local_16c,local_14);
                        puVar10 = (undefined4 *)((int)this + local_18 * 0x14 + 0x1c);
                        for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
                          *puVar10 = *puVar3;
                          puVar3 = puVar3 + 1;
                          puVar10 = puVar10 + 1;
                        }
                        BandStat::~BandStat(local_16c);
                        uVar2 = FUN_1001bb80(local_88,local_14);
                        iVar1 = Wvfm::envi(*(Wvfm **)((int)this + 8),uVar2);
                        *(undefined1 *)((int)this + local_18 + 0xa01c) =
                             *(undefined1 *)(param_1 + -1 + iVar1);
                        local_18 = local_18 + 1;
                      }
                      else if (iVar1 == 2) {
                        if (local_34[local_14] <= _DAT_10038a80) {
                          iVar1 = FUN_1001bb80(local_88,local_14);
                          local_28[iVar1] = 5;
                        }
                        goto LAB_1001aab0;
                      }
                    }
                    free_vector(local_34,1,local_20);
                    local_34 = (float *)0x0;
                    free_matrix(local_90,1,local_20,1,2);
                    local_90 = (float **)0x0;
                    local_20 = local_18 - 1;
                    if ((int)local_20 < 2) {
                      local_170 = 0;
                      local_8 = (uint)local_8._1_3_ << 8;
                      FUN_1001dece((int)local_60);
                      local_8 = 0xffffffff;
                      FUN_1001dece((int)local_88);
                      uVar6 = local_170;
                    }
                    else {
                      if ((param_5 == 1) && ((*param_6 >> 2 & 1) != 0)) {
                        iVar1 = Wvfm::rows(*(Wvfm **)((int)this + 8));
                        free_ivector(local_28,1,iVar1);
                      }
                      else {
                        FUN_1001e34e(local_60,(int)this + 0x1c,local_20);
                        if (local_8c != 0) {
                          printf(s_after_omitokn__1__omits_processe_1003fc4c);
                          FUN_1001e8a8((int)local_60);
                        }
                        piVar4 = ivector(1,local_20);
                        local_24 = piVar4;
                        if (piVar4 == (int *)0x0) {
                          *(undefined4 *)this = 2;
                          local_174 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_174;
                        }
                        uVar2 = local_20;
                        iVar1 = SSNODE::SWold((SSNODE *)local_60);
                        iVar5 = Annotate::getNumCurrFix((Annotate *)local_60);
                        iVar1 = FUN_10019280(iVar5,iVar1,piVar4,uVar2);
                        if (iVar1 != 1) {
                          *(undefined4 *)this = 4;
                          free_ivector(local_24,1,local_20);
                          local_178 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_178;
                        }
                        piVar4 = ivector(1,local_20);
                        local_30 = piVar4;
                        if (piVar4 == (int *)0x0) {
                          *(undefined4 *)this = 2;
                          free_ivector(local_24,1,local_20);
                          local_17c = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_17c;
                        }
                        uVar2 = local_20;
                        iVar1 = Annotate::getNumFwhmGapLen((Annotate *)local_60);
                        iVar5 = Annotate::getNumCurrFix((Annotate *)local_60);
                        iVar1 = FUN_10019280(iVar5,iVar1,piVar4,uVar2);
                        if (iVar1 != 1) {
                          *(undefined4 *)this = 4;
                          free_ivector(local_24,1,local_20);
                          free_ivector(local_30,1,local_20);
                          local_180 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_180;
                        }
                        ppfVar7 = matrix(1,local_20,1,2);
                        iVar8 = (int)this + 0xa01c;
                        uVar2 = local_20;
                        local_90 = ppfVar7;
                        iVar1 = Annotate::getNumFwhmGapLen((Annotate *)local_60);
                        iVar5 = SSNODE::SWold((SSNODE *)local_60);
                        local_1c = FUN_10011150((int)local_24,(int)local_30,iVar5,iVar1,iVar8,uVar2,
                                                (int)ppfVar7);
                        free_ivector(local_30,1,local_20);
                        local_30 = (int *)0x0;
                        if (local_1c != 1) {
                          free_ivector(local_24,1,local_20);
                          free_matrix(local_90,1,local_20,1,2);
                          local_184 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_184;
                        }
                        puVar3 = FUN_1001bbe0(local_60,(undefined4 *)local_198,1);
                        puVar10 = (undefined4 *)((int)this + 0x30);
                        for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
                          *puVar10 = *puVar3;
                          puVar3 = puVar3 + 1;
                          puVar10 = puVar10 + 1;
                        }
                        BandStat::~BandStat(local_198);
                        local_18 = 2;
                        for (local_14 = 2; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                          iVar1 = ftol();
                          if (iVar1 == 2) {
                            local_f4 = local_14 + -1;
                            if (local_24[local_f4] == 0) {
                              *(undefined4 *)this = 4;
                              free_ivector(local_24,1,local_20);
                              free_matrix(local_90,1,local_20,1,2);
                              local_19c = 0;
                              local_8 = (uint)local_8._1_3_ << 8;
                              FUN_1001dece((int)local_60);
                              local_8 = 0xffffffff;
                              FUN_1001dece((int)local_88);
                              ExceptionList = local_10;
                              return local_19c;
                            }
                            iVar1 = FUN_1001bbc0(local_60,local_f4);
                            local_ec = (double)iVar1 / (double)local_24[local_f4];
                            local_f0 = ftol();
                            if (local_f0 < 1) {
                              *(undefined4 *)this = 4;
                              free_ivector(local_24,1,local_20);
                              free_matrix(local_90,1,local_20,1,2);
                              local_1a0 = 0;
                              local_8 = (uint)local_8._1_3_ << 8;
                              FUN_1001dece((int)local_60);
                              local_8 = 0xffffffff;
                              FUN_1001dece((int)local_88);
                              ExceptionList = local_10;
                              return local_1a0;
                            }
                            iVar1 = FUN_1001bbc0(local_60,local_f4);
                            local_e4 = (float)iVar1 / (float)local_f0;
                            iVar1 = FUN_1001bb80(local_60,local_f4);
                            local_e0 = (float)iVar1;
                            for (local_dc = 1; local_dc < local_f0; local_dc = local_dc + 1) {
                              local_e0 = local_e0 + local_e4;
                              local_f8 = ftol();
                              iVar1 = ftol();
                              uVar6 = 1;
                              iVar5 = (iVar1 - local_f8) + 1;
                              local_114 = iVar1;
                              local_110 = FUN_100197cf(this,local_f8,iVar1);
                              <>(local_10c,local_f8,local_110,iVar1,iVar5,uVar6);
                              local_8._0_1_ = 2;
                              pBVar9 = local_10c;
                              puVar3 = (undefined4 *)((int)this + local_18 * 0x14 + 0x1c);
                              for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
                                *puVar3 = *(undefined4 *)pBVar9;
                                pBVar9 = pBVar9 + 4;
                                puVar3 = puVar3 + 1;
                              }
                              local_18 = local_18 + 1;
                              if (0x7ff < local_18) {
                                *(undefined4 *)this = 3;
                                free_ivector(local_24,1,local_20);
                                free_matrix(local_90,1,local_20,1,2);
                                local_1a4 = 0;
                                local_8._0_1_ = 1;
                                BandStat::~BandStat(local_10c);
                                local_8 = (uint)local_8._1_3_ << 8;
                                FUN_1001dece((int)local_60);
                                local_8 = 0xffffffff;
                                FUN_1001dece((int)local_88);
                                ExceptionList = local_10;
                                return local_1a4;
                              }
                              local_8._0_1_ = 1;
                              BandStat::~BandStat(local_10c);
                            }
                          }
                          puVar3 = FUN_1001bbe0(local_60,(undefined4 *)local_1b8,local_14);
                          puVar10 = (undefined4 *)((int)this + local_18 * 0x14 + 0x1c);
                          for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
                            *puVar10 = *puVar3;
                            puVar3 = puVar3 + 1;
                            puVar10 = puVar10 + 1;
                          }
                          local_18 = local_18 + 1;
                          BandStat::~BandStat(local_1b8);
                          if (0x7ff < local_18) {
                            *(undefined4 *)this = 3;
                            free_ivector(local_24,1,local_20);
                            free_matrix(local_90,1,local_20,1,2);
                            local_1bc = 0;
                            local_8 = (uint)local_8._1_3_ << 8;
                            FUN_1001dece((int)local_60);
                            local_8 = 0xffffffff;
                            FUN_1001dece((int)local_88);
                            ExceptionList = local_10;
                            return local_1bc;
                          }
                        }
                        free_ivector(local_24,1,local_20);
                        local_24 = (int *)0x0;
                        free_matrix(local_90,1,local_20,1,2);
                        local_90 = (float **)0x0;
                        local_20 = local_18 - 1;
                        if ((int)local_20 < 2) {
                          local_1c0 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_1c0;
                        }
                        FUN_1001e34e(local_60,(int)this + 0x1c,local_20);
                        if (local_8c != 0) {
                          printf(s_peaks_after_gapcheck___1003fc70);
                          FUN_1001e8a8((int)local_60);
                        }
                        piVar4 = ivector(1,local_20);
                        local_24 = piVar4;
                        if (piVar4 == (int *)0x0) {
                          *(undefined4 *)this = 2;
                          local_1c4 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_1c4;
                        }
                        uVar2 = local_20;
                        iVar1 = SSNODE::SWold((SSNODE *)local_60);
                        iVar5 = Annotate::getNumCurrFix((Annotate *)local_60);
                        iVar1 = FUN_10019280(iVar5,iVar1,piVar4,uVar2);
                        if (iVar1 != 1) {
                          *(undefined4 *)this = 4;
                          free_ivector(local_24,1,local_20);
                          local_1c8 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_1c8;
                        }
                        local_34 = FUN_10024e47(this,(Annotate *)local_60);
                        if (local_34 == (float *)0x0) {
                          *(undefined4 *)this = 2;
                          free_ivector(local_24,1,local_20);
                          local_1cc = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_1cc;
                        }
                        local_38 = vector(1,local_20);
                        if (local_38 == (float *)0x0) {
                          *(undefined4 *)this = 2;
                          free_ivector(local_24,1,local_20);
                          free_vector(local_34,1,local_20);
                          local_1d0 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_1d0;
                        }
                        for (local_14 = 1; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                          uVar2 = FUN_1001bb80(local_60,local_14);
                          dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
                          local_38[local_14] = (float)dVar11;
                        }
                        local_2c = vector(1,local_20);
                        if (local_2c == (float *)0x0) {
                          *(undefined4 *)this = 2;
                          free_ivector(local_24,1,local_20);
                          free_vector(local_34,1,local_20);
                          free_vector(local_38,1,local_20);
                          local_1d4 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_1d4;
                        }
                        for (local_14 = 1; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                          uVar2 = FUN_1001bb60(local_60,local_14);
                          dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
                          local_118 = (float)dVar11;
                          uVar2 = FUN_1001bba0(local_60,local_14);
                          dVar11 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar2);
                          local_11c = (float)dVar11;
                          local_230 = local_11c;
                          if (local_118 < local_11c) {
                            local_230 = local_118;
                          }
                          local_2c[local_14] = local_230;
                        }
                        ppfVar7 = matrix(1,local_20,1,2);
                        pfVar13 = local_34;
                        uVar2 = local_20;
                        local_90 = ppfVar7;
                        iVar1 = FUN_1001bcd0((int)local_60);
                        iVar5 = SSNODE::SWold((SSNODE *)local_60);
                        local_1c = FUN_10012140((int)local_24,local_38,(int)local_2c,iVar5,iVar1,
                                                pfVar13,uVar2,(int)ppfVar7);
                        free_vector(local_38,1,local_20);
                        local_38 = (float *)0x0;
                        free_vector(local_2c,1,local_20);
                        local_2c = (float *)0x0;
                        free_ivector(local_24,1,local_20);
                        local_24 = (int *)0x0;
                        if (local_1c != 1) {
                          free_vector(local_34,1,local_20);
                          local_34 = (float *)0x0;
                          free_matrix(local_90,1,local_20,1,2);
                          local_1d8 = 0;
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return local_1d8;
                        }
                        local_18 = 1;
                        for (local_14 = 1; local_14 <= (int)local_20; local_14 = local_14 + 1) {
                          local_120 = FUN_1001bb80(local_60,local_14);
                          iVar1 = ftol();
                          if (iVar1 == 1) {
LAB_1001b912:
                            puVar3 = FUN_1001bbe0(local_60,(undefined4 *)local_1ec,local_14);
                            puVar10 = (undefined4 *)((int)this + local_18 * 0x14 + 0x1c);
                            for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
                              *puVar10 = *puVar3;
                              puVar3 = puVar3 + 1;
                              puVar10 = puVar10 + 1;
                            }
                            BandStat::~BandStat(local_1ec);
                            *(undefined1 *)((int)this + local_18 + 0xa01c) =
                                 *(undefined1 *)(param_1 + -1 + local_28[local_120]);
                            local_18 = local_18 + 1;
                          }
                          else if (iVar1 == 2) {
                            if (local_34[local_14] <= _DAT_10038a80) {
                              local_28[local_120] = 5;
                            }
                            goto LAB_1001b912;
                          }
                        }
                        free_vector(local_34,1,local_20);
                        local_34 = (float *)0x0;
                        free_matrix(local_90,1,local_20,1,2);
                        local_90 = (float **)0x0;
                        iVar1 = Wvfm::rows(*(Wvfm **)((int)this + 8));
                        free_ivector(local_28,1,iVar1);
                        local_28 = (int *)0x0;
                        local_20 = local_18 - 1;
                        if ((int)local_20 < 2) {
                          local_8 = (uint)local_8._1_3_ << 8;
                          FUN_1001dece((int)local_60);
                          local_8 = 0xffffffff;
                          FUN_1001dece((int)local_88);
                          ExceptionList = local_10;
                          return 0;
                        }
                      }
                      local_28 = (int *)0x0;
                      if (((param_5 == 1) && ((param_4 & 2) != 0)) && ((*param_6 >> 6 & 1) != 0)) {
                        FUN_10019991(this,param_1,(int *)&local_20,100,1000);
                      }
                      FUN_1001e34e(local_60,(int)this + 0x1c,local_20);
                      if (local_8c != 0) {
                        printf(s_peaks_after_omitokn__2__1003fc8c);
                        FUN_1001e8a8((int)local_60);
                      }
                      uVar6 = FUN_1002552a(this,(Annotate *)local_60,param_2,(int)this + 0xa01c,
                                           param_4);
                      local_8 = (uint)local_8._1_3_ << 8;
                      FUN_1001dece((int)local_60);
                      local_8 = 0xffffffff;
                      FUN_1001dece((int)local_88);
                    }
                  }
                  else {
                    iVar1 = Wvfm::rows(*(Wvfm **)((int)this + 8));
                    free_ivector(local_28,1,iVar1);
                    free_vector(local_34,1,local_20);
                    local_34 = (float *)0x0;
                    free_matrix(local_90,1,local_20,1,2);
                    *(undefined4 *)this = 4;
                    local_158 = 0;
                    local_8 = (uint)local_8._1_3_ << 8;
                    FUN_1001dece((int)local_60);
                    local_8 = 0xffffffff;
                    FUN_1001dece((int)local_88);
                    uVar6 = local_158;
                  }
                }
              }
            }
          }
        }
        else {
          *(undefined4 *)this = 4;
          free_ivector(local_24,1,local_20);
          local_144 = 0;
          local_8 = (uint)local_8._1_3_ << 8;
          FUN_1001dece((int)local_60);
          local_8 = 0xffffffff;
          FUN_1001dece((int)local_88);
          uVar6 = local_144;
        }
      }
    }
    else {
      *(undefined4 *)this = 3;
      local_13c = 0;
      local_8 = (uint)local_8._1_3_ << 8;
      FUN_1001dece((int)local_60);
      local_8 = 0xffffffff;
      FUN_1001dece((int)local_88);
      uVar6 = local_13c;
    }
  }
  else {
    local_124 = 0;
    local_8 = (uint)local_8._1_3_ << 8;
    FUN_1001dece((int)local_60);
    local_8 = 0xffffffff;
    FUN_1001dece((int)local_88);
    uVar6 = local_124;
  }
  ExceptionList = local_10;
  return uVar6;
}

//===== 0x1001baf5 =====

void FUN_1001baf5(void)

{
  FUN_1001baff();
  return;
}

//===== 0x1001baff =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1001baff(void)

{
  _DAT_10042048 = acos(-1.0);
  return;
}

//===== 0x1001bb20 =====

/* Library Function - Multiple Matches With Same Base Name
    public: __thiscall
   <lambda_0a97c9e57da7be065955385c79108ff2>::<lambda_0a97c9e57da7be065955385c79108ff2>(struct
   _iobuf * const &,struct __crt_locale_pointers * const &,unsigned __int64 const &,wchar_t const *
   const &,char * const &)
    public: __thiscall
   <lambda_0be4ab1c2a6918fda4e39227d83ea893>::<lambda_0be4ab1c2a6918fda4e39227d83ea893>(struct
   _iobuf * const &,struct __crt_locale_pointers * const &,unsigned __int64 const &,char const *
   const &,char * const &)
    public: __thiscall
   <lambda_21448eb78dd3c4a522ed7c65a98d88e6>::<lambda_21448eb78dd3c4a522ed7c65a98d88e6>(struct
   __crt_locale_pointers * const &,struct _iobuf * const &,unsigned __int64 const &,char const *
   const &,char * const &)
    public: __thiscall
   <lambda_2565fc715a641e539f44ad02d6823606>::<lambda_2565fc715a641e539f44ad02d6823606>(struct
   _iobuf * const &,struct __crt_locale_pointers * const &,unsigned __int64 const &,char const *
   const &,char * const &)
     28 names - too many to list
   
   Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug */

undefined4 * __thiscall
<>(void *this,undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
  undefined4 param_5)

{
  *(undefined4 *)this = param_1;
  *(undefined4 *)((int)this + 4) = param_2;
  *(undefined4 *)((int)this + 8) = param_3;
  *(undefined4 *)((int)this + 0xc) = param_4;
  *(undefined4 *)((int)this + 0x10) = param_5;
  return this;
}

//===== 0x1001bb60 =====

undefined4 __thiscall FUN_1001bb60(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 8) + param_1 * 4);
}

//===== 0x1001bb80 =====

undefined4 __thiscall FUN_1001bb80(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 4) + param_1 * 4);
}

//===== 0x1001bba0 =====

undefined4 __thiscall FUN_1001bba0(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 8) + 4 + param_1 * 4);
}

//===== 0x1001bbc0 =====

undefined4 __thiscall FUN_1001bbc0(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 0xc) + 4 + param_1 * 4);
}

//===== 0x1001bbe0 =====

undefined4 * __thiscall FUN_1001bbe0(void *this,undefined4 *param_1,int param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  int iVar6;
  BandStat *pBVar7;
  undefined4 *puVar8;
  BandStat local_24 [20];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_100370a7;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  uVar1 = FUN_1001bc90(this,param_2);
  uVar2 = FUN_1001bcb0(this,param_2);
  uVar3 = FUN_1001bba0(this,param_2);
  uVar4 = FUN_1001bb80(this,param_2);
  uVar5 = FUN_1001bb60(this,param_2);
  <>(local_24,uVar5,uVar4,uVar3,uVar2,uVar1);
  pBVar7 = local_24;
  puVar8 = param_1;
  for (iVar6 = 5; iVar6 != 0; iVar6 = iVar6 + -1) {
    *puVar8 = *(undefined4 *)pBVar7;
    pBVar7 = pBVar7 + 4;
    puVar8 = puVar8 + 1;
  }
  BandStat::~BandStat(local_24);
  ExceptionList = local_10;
  return param_1;
}

//===== 0x1001bc90 =====

undefined4 __thiscall FUN_1001bc90(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 0x14) + param_1 * 4);
}

//===== 0x1001bcb0 =====

undefined4 __thiscall FUN_1001bcb0(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 0x10) + param_1 * 4);
}

//===== 0x1001bcd0 =====

int __fastcall FUN_1001bcd0(int param_1)

{
  return *(int *)(param_1 + 0xc) + 4;
}

//===== 0x1001bcf0 =====

/* public: __thiscall ObsInpSpec::ObsInpSpec(void) */

ObsInpSpec * __thiscall ObsInpSpec::ObsInpSpec(ObsInpSpec *this)

{
  int iVar1;
  int local_c;
  int local_8;
  
                    /* 0x1bcf0  14  ??0ObsInpSpec@@QAE@XZ */
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x1c) = 0;
  *(undefined4 *)(this + 0x20) = 0;
  *(undefined4 *)(this + 0x24) = 0;
  *(undefined4 *)(this + 0x28) = 0;
  *(undefined4 *)(this + 0x4c) = 0;
  *(undefined4 *)(this + 0x50) = 0;
  *(undefined4 *)(this + 0x54) = 0;
  *(undefined4 *)(this + 0x58) = 0;
  *(undefined4 *)(this + 0x5c) = 0;
  *(undefined4 *)(this + 0x60) = 0;
  *(undefined4 *)(this + 100) = 0;
  *(undefined4 *)(this + 200) = 0;
  *(undefined4 *)(this + 0xcc) = 0;
  memset(this,0,6);
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    *(undefined4 *)(this + local_8 * 4 + 0x2c) = 0;
    *(undefined4 *)(this + local_8 * 4 + 0x3c) = 0;
  }
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    iVar1 = local_8 * 0x18;
    *(undefined4 *)(this + iVar1 + 0x78) = 0;
    *(undefined4 *)(this + iVar1 + 0x7c) = 0;
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      *(undefined4 *)(this + local_c * 4 + iVar1 + 0x68) = 0;
    }
  }
  *(undefined4 *)(this + 0xd0) = 0;
  *(undefined4 *)(this + 0xd4) = 0;
  *(undefined4 *)(this + 0xd8) = 0;
  *(undefined4 *)(this + 0xdc) = 0;
  *(undefined4 *)(this + 0xe0) = 0;
  *(undefined4 *)(this + 0xe4) = 0;
  return this;
}

//===== 0x1001beb3 =====

/* public: __thiscall ObsInpSpec::~ObsInpSpec(void) */

void __thiscall ObsInpSpec::~ObsInpSpec(ObsInpSpec *this)

{
                    /* 0x1beb3  36  ??1ObsInpSpec@@QAE@XZ */
  release(this);
  return;
}

//===== 0x1001bec6 =====

/* public: class ObsInpSpec const & __thiscall ObsInpSpec::operator=(class ObsInpSpec const &) */

ObsInpSpec * __thiscall ObsInpSpec::operator=(ObsInpSpec *this,ObsInpSpec *param_1)

{
  undefined4 uVar1;
  void *pvVar2;
  int iVar3;
  int iVar4;
  int local_1c;
  int local_18;
  int local_c;
  int local_8;
  
                    /* 0x1bec6  49  ??4ObsInpSpec@@QAEABV0@ABV0@@Z */
  if (param_1 != this) {
    release(this);
    *(undefined4 *)(this + 8) = *(undefined4 *)(param_1 + 8);
    *(undefined4 *)(this + 0xc) = *(undefined4 *)(param_1 + 0xc);
    *(undefined4 *)(this + 0x10) = *(undefined4 *)(param_1 + 0x10);
    *(undefined4 *)(this + 0x14) = *(undefined4 *)(param_1 + 0x14);
    *(undefined4 *)(this + 0x18) = *(undefined4 *)(param_1 + 0x18);
    *(undefined4 *)(this + 0x1c) = *(undefined4 *)(param_1 + 0x1c);
    *(undefined4 *)(this + 0x20) = *(undefined4 *)(param_1 + 0x20);
    *(undefined4 *)(this + 0x24) = *(undefined4 *)(param_1 + 0x24);
    *(undefined4 *)(this + 0x28) = *(undefined4 *)(param_1 + 0x28);
    *(undefined4 *)(this + 0x4c) = *(undefined4 *)(param_1 + 0x4c);
    *(undefined4 *)(this + 0x50) = *(undefined4 *)(param_1 + 0x50);
    *(undefined4 *)(this + 0x54) = *(undefined4 *)(param_1 + 0x54);
    *(undefined4 *)(this + 0x58) = *(undefined4 *)(param_1 + 0x58);
    *(undefined4 *)(this + 0x5c) = *(undefined4 *)(param_1 + 0x5c);
    *(undefined4 *)(this + 0x60) = *(undefined4 *)(param_1 + 0x60);
    *(undefined4 *)(this + 100) = *(undefined4 *)(param_1 + 100);
    *(undefined4 *)(this + 200) = *(undefined4 *)(param_1 + 200);
    *(undefined4 *)(this + 0xcc) = *(undefined4 *)(param_1 + 0xcc);
    memcpy(this,param_1,6);
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      *(undefined4 *)(this + local_8 * 4 + 0x2c) = *(undefined4 *)(param_1 + local_8 * 4 + 0x2c);
      *(undefined4 *)(this + local_8 * 4 + 0x3c) = *(undefined4 *)(param_1 + local_8 * 4 + 0x3c);
    }
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      iVar3 = local_8 * 0x18;
      iVar4 = local_8 * 0x18;
      *(undefined4 *)(this + iVar4 + 0x78) = *(undefined4 *)(param_1 + iVar3 + 0x78);
      *(undefined4 *)(this + iVar4 + 0x7c) = *(undefined4 *)(param_1 + iVar3 + 0x7c);
      for (local_c = 0; local_c < 4; local_c = local_c + 1) {
        *(undefined4 *)(this + local_c * 4 + iVar4 + 0x68) =
             *(undefined4 *)(param_1 + local_c * 4 + iVar3 + 0x68);
      }
    }
    *(undefined4 *)(this + 0xd0) = *(undefined4 *)(param_1 + 0xd0);
    if (*(int *)(this + 0xd0) != 0) {
      pvVar2 = operator_new(*(int *)(this + 0xd0) << 3);
      *(void **)(this + 0xd4) = pvVar2;
      pvVar2 = operator_new(*(int *)(this + 0xd0) << 3);
      *(void **)(this + 0xd8) = pvVar2;
      pvVar2 = operator_new(*(int *)(this + 0xd0) << 3);
      *(void **)(this + 0xdc) = pvVar2;
      pvVar2 = operator_new(*(int *)(this + 0xd0) << 3);
      *(void **)(this + 0xe0) = pvVar2;
      pvVar2 = operator_new(*(int *)(this + 0xd0) << 3);
      *(void **)(this + 0xe4) = pvVar2;
      for (local_1c = 0; local_1c < *(int *)(this + 0xd0); local_1c = local_1c + 1) {
        uVar1 = *(undefined4 *)(*(int *)(param_1 + 0xd4) + 4 + local_1c * 8);
        iVar3 = *(int *)(this + 0xd4);
        *(undefined4 *)(iVar3 + local_1c * 8) =
             *(undefined4 *)(*(int *)(param_1 + 0xd4) + local_1c * 8);
        *(undefined4 *)(iVar3 + 4 + local_1c * 8) = uVar1;
        for (local_18 = 0; local_18 < 4; local_18 = local_18 + 1) {
          uVar1 = *(undefined4 *)(*(int *)(param_1 + local_18 * 4 + 0xd8) + 4 + local_1c * 8);
          iVar3 = *(int *)(this + local_18 * 4 + 0xd8);
          *(undefined4 *)(iVar3 + local_1c * 8) =
               *(undefined4 *)(*(int *)(param_1 + local_18 * 4 + 0xd8) + local_1c * 8);
          *(undefined4 *)(iVar3 + 4 + local_1c * 8) = uVar1;
        }
      }
    }
  }
  return this;
}

//===== 0x1001c1ef =====

/* public: __thiscall ObsInpSpec::ObsInpSpec(class ObsInpSpec const &) */

ObsInpSpec * __thiscall ObsInpSpec::ObsInpSpec(ObsInpSpec *this,ObsInpSpec *param_1)

{
                    /* 0x1c1ef  13  ??0ObsInpSpec@@QAE@ABV0@@Z */
  *(undefined4 *)(this + 0xd4) = 0;
  *(undefined4 *)(this + 0xd8) = 0;
  *(undefined4 *)(this + 0xdc) = 0;
  *(undefined4 *)(this + 0xe0) = 0;
  *(undefined4 *)(this + 0xe4) = 0;
  operator=(this,param_1);
  return this;
}

//===== 0x1001c24c =====

/* public: void __thiscall ObsInpSpec::laneOrder(char const *) */

void __thiscall ObsInpSpec::laneOrder(ObsInpSpec *this,char *param_1)

{
                    /* 0x1c24c  255  ?laneOrder@ObsInpSpec@@QAEXPBD@Z */
  strncpy((char *)this,param_1,6);
  return;
}

//===== 0x1001c26c =====

/* public: void __thiscall ObsInpSpec::boundaries(int,int,int) */

void __thiscall ObsInpSpec::boundaries(ObsInpSpec *this,int param_1,int param_2,int param_3)

{
                    /* 0x1c26c  93  ?boundaries@ObsInpSpec@@QAEXHHH@Z */
  *(int *)(this + 8) = param_1;
  *(int *)(this + 0xc) = param_2;
  *(int *)(this + 0x10) = param_3;
  return;
}

//===== 0x1001c294 =====

/* public: void __thiscall ObsInpSpec::lmBoundaries(int,int,int) */

void __thiscall ObsInpSpec::lmBoundaries(ObsInpSpec *this,int param_1,int param_2,int param_3)

{
                    /* 0x1c294  265  ?lmBoundaries@ObsInpSpec@@QAEXHHH@Z */
  *(int *)(this + 0x14) = param_1;
  *(int *)(this + 0x18) = param_2;
  *(int *)(this + 0x1c) = param_3;
  return;
}

//===== 0x1001c2bc =====

/* public: void __thiscall ObsInpSpec::widthDataPt(int,float) */

void __thiscall ObsInpSpec::widthDataPt(ObsInpSpec *this,int param_1,float param_2)

{
  int iVar1;
  
                    /* 0x1c2bc  440  ?widthDataPt@ObsInpSpec@@QAEXHM@Z */
  if (param_1 < 0x65) {
    iVar1 = ftol();
    *(int *)(this + 0x2c) = *(int *)(this + 0x2c) + iVar1;
    *(int *)(this + 0x3c) = *(int *)(this + 0x3c) + 1;
  }
  else if (param_1 < 0xc9) {
    iVar1 = ftol();
    *(int *)(this + 0x30) = *(int *)(this + 0x30) + iVar1;
    *(int *)(this + 0x40) = *(int *)(this + 0x40) + 1;
  }
  else if (param_1 < 0x191) {
    iVar1 = ftol();
    *(int *)(this + 0x34) = *(int *)(this + 0x34) + iVar1;
    *(int *)(this + 0x44) = *(int *)(this + 0x44) + 1;
  }
  else {
    iVar1 = ftol();
    *(int *)(this + 0x38) = *(int *)(this + 0x38) + iVar1;
    *(int *)(this + 0x48) = *(int *)(this + 0x48) + 1;
  }
  return;
}

//===== 0x1001c37e =====

/* public: void __thiscall ObsInpSpec::decimateData(int,int,float,float) */

void __thiscall
ObsInpSpec::decimateData(ObsInpSpec *this,int param_1,int param_2,float param_3,float param_4)

{
                    /* 0x1c37e  134  ?decimateData@ObsInpSpec@@QAEXHHMM@Z */
  *(int *)(this + 0x4c) = param_1;
  *(int *)(this + 0x50) = param_2;
  *(float *)(this + 0x58) = param_3;
  *(float *)(this + 0x5c) = param_4;
  return;
}

//===== 0x1001c3af =====

/* public: void __thiscall ObsInpSpec::rateChgAction(enum ObsInpSpec::RC_ACTION,int) */

void __thiscall ObsInpSpec::rateChgAction(ObsInpSpec *this,RC_ACTION param_1,int param_2)

{
                    /* 0x1c3af  327  ?rateChgAction@ObsInpSpec@@QAEXW4RC_ACTION@1@H@Z */
  *(RC_ACTION *)(this + 0x60) = param_1;
  *(int *)(this + 0x54) = param_2;
  return;
}

//===== 0x1001c3ce =====

/* public: void __thiscall ObsInpSpec::debug(void)const  */

void __thiscall ObsInpSpec::debug(ObsInpSpec *this)

{
  ObsInpSpec *pOVar1;
  double dVar2;
  int local_4c;
  int local_48;
  float afStack_44 [16];
  
                    /* 0x1c3ce  127  ?debug@ObsInpSpec@@QBEXXZ */
  printf(s_ObsInpSpec____p_1003fd28);
  printf(s_GENERAL_INFORMATION__1003fd3c);
  printf(s_laneOrder____s_1003fd54);
  printf(s_bgnScnl____5d_1003fd68);
  printf(s_endScnl____5d_1003fd80);
  printf(s_totScnl____5d_1003fd98);
  printf(s_meas__rng_____4d___4d__1003fdb0,*(undefined4 *)(this + 0x20));
  printf(s_POST_INTERPOLATION_DECIMATION__1003fdcc);
  printf(s_bgnScnl____5d_1003fdf0);
  printf(s_endScnl____5d_1003fe08);
  printf(s_totScnl____5d_1003fe20);
  printf(s_BAND_DENSITY_MEASUREMENTS_USED_I_1003fe38);
  printf(s__Peaks__total____4d_1003fe7c);
  printf(s__Peaks__check____3d_1003fe98);
  printf(s_checked_uWidth____1f_1003feb4,(double)*(float *)(this + 0x58));
  printf(s_checked_stdev____2f_1003fed0,(double)*(float *)(this + 0x5c));
  printf(s_action_taken___s__by__d__1003feec,(&PTR_s_No_Change_1003fcf8)[*(int *)(this + 0x60)]);
  printf(s_OVERALL_BAND_DENSITY_PROFILES____1003ff10);
  printf(s_BgnPk_EndPk_scnlPerBand_bandsPer_1003ff40);
  if (*(int *)(this + 0x3c) == 0) {
    printf(s_1_100_0_0_1003ff94);
  }
  else {
    printf(s_1_100__3d__3d_1003ff6c,*(int *)(this + 0x2c) / *(int *)(this + 0x3c));
  }
  if (*(int *)(this + 0x40) == 0) {
    printf(s_101_200_0_0_1003ffe4);
  }
  else {
    printf(s_101_200__3d__3d_1003ffbc,*(int *)(this + 0x30) / *(int *)(this + 0x40));
  }
  if (*(int *)(this + 0x44) == 0) {
    printf(s_201_400_0_0_10040034);
  }
  else {
    printf(s_201_400__3d__3d_1004000c,*(int *)(this + 0x34) / *(int *)(this + 0x44));
  }
  if (*(int *)(this + 0x48) == 0) {
    printf(s_401_N_0_0_10040084);
  }
  else {
    printf(s_401__4d__3d__3d_1004005c);
  }
  printf(s_WAX_AND_WANE_OF_BAND_RESOLUTION_100400ac);
  printf(s_waxes____4d_wanes____4d_100400d0,*(undefined4 *)(this + 200));
  printf(s_OBSERVED_FLUOR_RATIOS___100400f4);
  printf(s__ratios_used___3d_10040110);
  printf(s__c__c__c__c_freq_uAngl_10040128,(int)(char)*this,(int)(char)this[1],(int)(char)this[2]);
  for (local_48 = 0; local_48 < 4; local_48 = local_48 + 1) {
    pOVar1 = this + local_48 * 0x18 + 0x68;
    printf(s___2f___2f___2f___2f__3d__3d_10040154,(double)*(float *)pOVar1,
           (double)*(float *)(pOVar1 + 4),(double)*(float *)(pOVar1 + 8),
           (double)*(float *)(pOVar1 + 0xc),*(float *)(pOVar1 + 0x10));
  }
  printf(&DAT_1004017c);
  printf(s_CORRCOEF_OF_FLUOR_RATIOS___10040180);
  for (local_48 = 0; local_48 < 4; local_48 = local_48 + 1) {
    afStack_44[local_48 * 5] = 1.0;
    local_4c = local_48;
    while (local_4c = local_4c + 1, local_4c < 4) {
      dVar2 = corrcoef((float *)(this + local_48 * 0x18 + 0x68),
                       (float *)(this + local_4c * 0x18 + 0x68),4);
      afStack_44[local_4c * 4 + local_48] = (float)dVar2;
      afStack_44[local_48 * 4 + local_4c] = afStack_44[local_4c * 4 + local_48];
    }
  }
  for (local_48 = 0; local_48 < 4; local_48 = local_48 + 1) {
    printf(s__100401a0);
    for (local_4c = 0; local_4c < 4; local_4c = local_4c + 1) {
      printf(s__5_2f_100401a8,(double)afStack_44[local_48 * 4 + local_4c]);
    }
    printf(&DAT_100401b0);
  }
  printf(&DAT_100401b4);
  printf(s_CARL_FULLER_S_N_MEASUREMENTS___100401b8);
  printf(s_Bgn_End_sig1_noi1_S_N_sig2_noi2_S_100401dc);
  for (local_48 = 0; local_48 < *(int *)(this + 0xd0); local_48 = local_48 + 1) {
    printf(s__4d__4d_1004022c,*(undefined4 *)(*(int *)(this + 0xd4) + local_48 * 8));
    for (local_4c = 0; local_4c < 4; local_4c = local_4c + 1) {
      if (*(int *)(*(int *)(this + local_4c * 4 + 0xd8) + 4 + local_48 * 8) == 0) {
        printf(s__4d__4d_0_0_1004023c,
               *(undefined4 *)(*(int *)(this + local_4c * 4 + 0xd8) + local_48 * 8));
      }
      else {
        ftol();
        printf(s__4d__4d__3d_1004024c);
      }
    }
    printf(&DAT_1004025c);
  }
  printf(&DAT_10040260);
  return;
}

//===== 0x1001c9c4 =====

void FUN_1001c9c4(void)

{
  FUN_1001c9ce();
  return;
}

//===== 0x1001c9ce =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1001c9ce(void)

{
  _DAT_100420b0 = acos(-1.0);
  return;
}

//===== 0x1001c9e8 =====

/* public: void __thiscall ObsInpSpec::setCFTblLen(int) */

void __thiscall ObsInpSpec::setCFTblLen(ObsInpSpec *this,int param_1)

{
  void *pvVar1;
  
                    /* 0x1c9e8  360  ?setCFTblLen@ObsInpSpec@@QAEXH@Z */
  if (*(int *)(this + 0xd0) != 0) {
    operator_delete(*(void **)(this + 0xd4));
    operator_delete(*(void **)(this + 0xd8));
    operator_delete(*(void **)(this + 0xdc));
    operator_delete(*(void **)(this + 0xe0));
    operator_delete(*(void **)(this + 0xe4));
  }
  *(int *)(this + 0xd0) = param_1;
  if (*(int *)(this + 0xd0) != 0) {
    pvVar1 = operator_new(*(int *)(this + 0xd0) << 3);
    *(void **)(this + 0xd4) = pvVar1;
    pvVar1 = operator_new(*(int *)(this + 0xd0) << 3);
    *(void **)(this + 0xd8) = pvVar1;
    pvVar1 = operator_new(*(int *)(this + 0xd0) << 3);
    *(void **)(this + 0xdc) = pvVar1;
    pvVar1 = operator_new(*(int *)(this + 0xd0) << 3);
    *(void **)(this + 0xe0) = pvVar1;
    pvVar1 = operator_new(*(int *)(this + 0xd0) << 3);
    *(void **)(this + 0xe4) = pvVar1;
  }
  return;
}

//===== 0x1001cb2d =====

/* public: void __thiscall ObsInpSpec::setCFTblBndry(int,int,int) */

void __thiscall ObsInpSpec::setCFTblBndry(ObsInpSpec *this,int param_1,int param_2,int param_3)

{
                    /* 0x1cb2d  358  ?setCFTblBndry@ObsInpSpec@@QAEXHHH@Z */
  if ((-1 < param_1) && (param_1 < *(int *)(this + 0xd0))) {
    *(int *)(*(int *)(this + 0xd4) + param_1 * 8) = param_2;
    *(int *)(*(int *)(this + 0xd4) + 4 + param_1 * 8) = param_3;
  }
  return;
}

//===== 0x1001cb73 =====

/* public: void __thiscall ObsInpSpec::setCFTblEntry(int,int,int,int) */

void __thiscall
ObsInpSpec::setCFTblEntry(ObsInpSpec *this,int param_1,int param_2,int param_3,int param_4)

{
                    /* 0x1cb73  359  ?setCFTblEntry@ObsInpSpec@@QAEXHHHH@Z */
  if ((((-1 < param_1) && (param_1 < 4)) && (-1 < param_2)) && (param_2 < *(int *)(this + 0xd0))) {
    *(int *)(*(int *)(this + param_1 * 4 + 0xd8) + param_2 * 8) = param_3;
    *(int *)(*(int *)(this + param_1 * 4 + 0xd8) + 4 + param_2 * 8) = param_4;
  }
  return;
}

//===== 0x1001cbcd =====

/* private: void __thiscall ObsInpSpec::release(void) */

void __thiscall ObsInpSpec::release(ObsInpSpec *this)

{
  int local_8;
  
                    /* 0x1cbcd  334  ?release@ObsInpSpec@@AAEXXZ */
  if (*(int *)(this + 0xd4) != 0) {
    operator_delete(*(void **)(this + 0xd4));
    *(undefined4 *)(this + 0xd4) = 0;
  }
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    if (*(int *)(this + local_8 * 4 + 0xd8) != 0) {
      operator_delete(*(void **)(this + local_8 * 4 + 0xd8));
      *(undefined4 *)(this + local_8 * 4 + 0xd8) = 0;
    }
  }
  return;
}

//===== 0x1001cc70 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall RdrOut::phredify(void) */

void __thiscall RdrOut::phredify(RdrOut *this)

{
  BandStatArray *this_00;
  int *piVar1;
  int *piVar2;
  void *pvVar3;
  float *pfVar4;
  int iVar5;
  int iVar6;
  int local_4c;
  int local_40;
  float local_24;
  int *local_20;
  float local_1c;
  undefined4 local_18;
  int local_10;
  undefined4 local_c;
  float *local_8;
  
                    /* 0x1cc70  299  ?phredify@RdrOut@@AAEXXZ */
  local_20 = (int *)0x0;
  this_00 = bandstat(this);
  local_40 = Wvfm::annotate((Wvfm *)this_00);
  local_40 = local_40 + -1;
  local_10 = 0;
  if (99 < local_40) {
    if (0x96 < local_40) {
      local_40 = 0x96;
    }
    piVar1 = operator_new(local_40 << 2);
    local_20 = operator_new(local_40 << 2);
    piVar2 = operator_new(local_40 << 2);
    pvVar3 = operator_new(local_40 * 0xc);
    pfVar4 = vector(1,local_40);
    local_8 = vector(1,local_40);
    for (local_4c = 0; local_4c < local_40; local_4c = local_4c + 1) {
      iVar5 = BandStatArray::posn(this_00,local_4c);
      piVar2[local_4c] = iVar5;
      iVar5 = BandStatArray::posn(this_00,local_4c + 1);
      iVar6 = BandStatArray::posn(this_00,local_4c);
      piVar1[local_4c] = iVar5 - iVar6;
      iVar5 = BandStatArray::bbgn(this_00,local_4c);
      *(int *)((int)pvVar3 + local_4c * 0xc) = iVar5;
      iVar5 = BandStatArray::posn(this_00,local_4c);
      *(int *)((int)pvVar3 + local_4c * 0xc + 4) = iVar5;
      iVar5 = BandStatArray::bend(this_00,local_4c);
      *(int *)((int)pvVar3 + local_4c * 0xc + 8) = iVar5;
      pfVar4[local_4c + 1] = (float)local_4c;
      local_8[local_4c + 1] = (float)piVar1[local_4c];
    }
    polfit(pfVar4,local_8,(float *)0x0,local_40,2,0,&local_1c,&local_24);
    local_c = local_18;
    for (local_4c = 0; local_4c < local_40; local_4c = local_4c + 1) {
      iVar5 = ftol();
      local_20[local_4c] = iVar5;
      if ((piVar1[local_4c] + local_20[local_4c] < 1) || (piVar1[local_4c] < 1)) {
        fprintf((FILE *)(_iob_exref + 0x40),s_Warning__phredify___quit__100402b0);
        free_vector(pfVar4,1,local_40);
        free_vector(local_8,1,local_40);
        goto LAB_1001d0ee;
      }
      local_10 = local_10 + local_20[local_4c];
    }
    free_vector(pfVar4,1,local_40);
    free_vector(local_8,1,local_40);
    Wvfm::chgGaps((Wvfm *)(this + 0x28),piVar2,piVar1,local_20,pvVar3,local_40,local_10);
    for (local_4c = 0; local_4c < local_40; local_4c = local_4c + 1) {
      BandStatArray::bbgn(this_00,local_4c,*(int *)((int)pvVar3 + local_4c * 0xc));
      BandStatArray::posn(this_00,local_4c,*(int *)((int)pvVar3 + local_4c * 0xc + 4));
      BandStatArray::bend(this_00,local_4c,*(int *)((int)pvVar3 + local_4c * 0xc + 8));
    }
    iVar5 = BandStatArray::bend(this_00,local_4c + -1);
    BandStatArray::bbgn(this_00,local_4c,iVar5);
    iVar5 = BandStatArray::posn(this_00,local_4c);
    BandStatArray::posn(this_00,local_4c,iVar5 + local_10);
    iVar5 = BandStatArray::bend(this_00,local_4c);
    BandStatArray::bend(this_00,local_4c,iVar5 + local_10);
    while( true ) {
      local_4c = local_4c + 1;
      iVar5 = Wvfm::annotate((Wvfm *)this_00);
      if (iVar5 <= local_4c) break;
      iVar5 = BandStatArray::bbgn(this_00,local_4c);
      BandStatArray::bbgn(this_00,local_4c,iVar5 + local_10);
      iVar5 = BandStatArray::posn(this_00,local_4c);
      BandStatArray::posn(this_00,local_4c,iVar5 + local_10);
      iVar5 = BandStatArray::bend(this_00,local_4c);
      BandStatArray::bend(this_00,local_4c,iVar5 + local_10);
    }
LAB_1001d0ee:
    operator_delete(piVar1);
    operator_delete(local_20);
    operator_delete(piVar2);
    operator_delete(pvVar3);
  }
  return;
}

//===== 0x1001d13f =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall RdrOut::phredify2(int,int) */

void __thiscall RdrOut::phredify2(RdrOut *this,int param_1,int param_2)

{
  float fVar1;
  BandStatArray *this_00;
  int iVar2;
  int *piVar3;
  int *piVar4;
  void *pvVar5;
  float *pfVar6;
  int iVar7;
  int iVar8;
  int local_4c;
  float local_3c;
  float local_28;
  float local_24;
  int *local_20;
  float local_1c;
  float local_18;
  float local_14;
  float local_10;
  int local_c;
  float *local_8;
  
                    /* 0x1d13f  298  ?phredify2@RdrOut@@AAEXHH@Z */
  local_8 = (float *)0x0;
  local_20 = (int *)0x0;
  this_00 = bandstat(this);
  iVar2 = Wvfm::annotate((Wvfm *)this_00);
  iVar2 = iVar2 + -1;
  local_c = 0;
  if (99 < iVar2) {
    piVar3 = operator_new(iVar2 * 4);
    local_20 = operator_new(iVar2 * 4);
    piVar4 = operator_new(iVar2 * 4);
    pvVar5 = operator_new(iVar2 * 0xc);
    pfVar6 = vector(1,iVar2);
    local_8 = vector(1,iVar2);
    for (local_4c = 0; local_4c < iVar2; local_4c = local_4c + 1) {
      iVar7 = BandStatArray::posn(this_00,local_4c);
      piVar4[local_4c] = iVar7;
      iVar7 = BandStatArray::posn(this_00,local_4c + 1);
      iVar8 = BandStatArray::posn(this_00,local_4c);
      piVar3[local_4c] = iVar7 - iVar8;
      iVar7 = BandStatArray::bbgn(this_00,local_4c);
      *(int *)((int)pvVar5 + local_4c * 0xc) = iVar7;
      iVar7 = BandStatArray::posn(this_00,local_4c);
      *(int *)((int)pvVar5 + local_4c * 0xc + 4) = iVar7;
      iVar7 = BandStatArray::bend(this_00,local_4c);
      *(int *)((int)pvVar5 + local_4c * 0xc + 8) = iVar7;
      pfVar6[local_4c + 1] = (float)local_4c;
      local_8[local_4c + 1] = (float)piVar3[local_4c];
    }
    polfit(pfVar6,local_8,(float *)0x0,iVar2,3,0,&local_1c,&local_28);
    local_3c = local_18;
    local_24 = local_18;
    for (local_4c = 1; local_4c < iVar2; local_4c = local_4c + 1) {
      fVar1 = (float)local_4c;
      fVar1 = local_10 * fVar1 * fVar1 + local_14 * fVar1 + local_18;
      if (local_24 < fVar1) {
        local_24 = fVar1;
      }
      if (fVar1 < local_3c) {
        local_3c = fVar1;
      }
    }
    if (local_24 != local_3c) {
      for (local_4c = 0; local_4c < iVar2; local_4c = local_4c + 1) {
        iVar7 = ftol();
        local_20[local_4c] = iVar7;
        iVar7 = piVar3[local_4c];
        if ((iVar7 + local_20[local_4c] < 1) || (iVar7 < 1)) {
          fprintf((FILE *)(_iob_exref + 0x40),s_Warning__phredify2___quit__tstL__100402cc,
                  iVar7 + local_20[local_4c],iVar7);
          goto LAB_1001d54f;
        }
        local_c = local_c + local_20[local_4c];
      }
      Wvfm::chgGaps((Wvfm *)(this + 0x28),piVar4,piVar3,local_20,pvVar5,iVar2,local_c);
      for (local_4c = 0; local_4c < iVar2; local_4c = local_4c + 1) {
        BandStatArray::bbgn(this_00,local_4c,*(int *)((int)pvVar5 + local_4c * 0xc));
        BandStatArray::posn(this_00,local_4c,*(int *)((int)pvVar5 + local_4c * 0xc + 4));
        BandStatArray::bend(this_00,local_4c,*(int *)((int)pvVar5 + local_4c * 0xc + 8));
      }
      BandStatArray::declen(this_00);
    }
LAB_1001d54f:
    operator_delete(piVar3);
    operator_delete(local_20);
    operator_delete(piVar4);
    operator_delete(pvVar5);
    free_vector(pfVar6,1,iVar2);
    free_vector(local_8,1,iVar2);
  }
  return;
}

//===== 0x1001d5ce =====

/* public: void __thiscall Wvfm::chgGaps(int const *,int const *,int const *,void *,int,int) */

void __thiscall
Wvfm::chgGaps(Wvfm *this,int *param_1,int *param_2,int *param_3,void *param_4,int param_5,
             int param_6)

{
  float fVar1;
  double dVar2;
  LMConvert local_a0 [36];
  int local_7c;
  int local_78;
  LMConvert local_74 [36];
  int local_50;
  int local_4c;
  int local_48;
  long local_44;
  int local_40;
  ShftVect local_3c [8];
  int local_34;
  int local_30;
  double **local_2c;
  float *local_28;
  int local_24;
  int local_20;
  int local_1c;
  void *local_18;
  float *local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x1d5ce  111  ?chgGaps@Wvfm@@QAEXPBH00PAXHH@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_100370d5;
  local_10 = ExceptionList;
  local_2c = (double **)0x0;
  local_28 = (float *)0x0;
  local_14 = (float *)0x0;
  ExceptionList = &local_10;
  ShftVect::ShftVect(local_3c);
  local_18 = param_4;
  local_44 = rows(this);
  local_30 = local_44 + param_6;
  local_2c = dmatrix(1,local_30,1,4);
  local_28 = vector(1,local_44);
  for (local_48 = 1; local_48 < 5; local_48 = local_48 + 1) {
    for (local_24 = 1; local_24 < *param_1; local_24 = local_24 + 1) {
      dVar2 = sc_la(this,local_24,local_48);
      local_2c[local_24][local_48] = dVar2;
    }
    local_20 = local_24;
    local_1c = 0;
    for (local_34 = 0; local_34 < param_5; local_34 = local_34 + 1) {
      if (local_48 == 1) {
        if (local_34 == 0) {
          *(int *)((int)local_18 + 8) = *(int *)((int)local_18 + 8) + *param_3 / 2;
        }
        else {
          *(undefined4 *)((int)local_18 + local_34 * 0xc) =
               *(undefined4 *)((int)local_18 + (local_34 + -1) * 0xc + 8);
          *(int *)((int)local_18 + local_34 * 0xc + 4) =
               *(int *)((int)local_18 + local_34 * 0xc + 4) + local_1c;
          *(int *)((int)local_18 + local_34 * 0xc + 8) =
               *(int *)((int)local_18 + local_34 * 0xc + 8) + local_1c + param_3[local_34] / 2;
        }
        local_1c = local_1c + param_3[local_34];
      }
      local_50 = param_2[local_34];
      local_4c = local_50 + param_3[local_34];
      for (local_40 = 0; local_40 <= local_50; local_40 = local_40 + 1) {
        dVar2 = sc_la(this,local_24,local_48);
        local_28[local_40] = (float)dVar2;
        local_24 = local_24 + 1;
      }
      local_24 = local_24 + -1;
      if (local_4c != local_50) {
        LMConvert::LMConvert(local_74,local_28,local_50 + 1,local_4c,local_50);
        local_8 = 0;
        for (local_40 = 0; local_40 < local_4c; local_40 = local_40 + 1) {
          fVar1 = LMConvert::output(local_74,local_40);
          local_28[local_40] = fVar1;
        }
        local_8 = 0xffffffff;
        LMConvert::~LMConvert(local_74);
      }
      for (local_40 = 0; local_40 < local_4c; local_40 = local_40 + 1) {
        local_2c[local_20][local_48] = (double)local_28[local_40];
        local_20 = local_20 + 1;
      }
    }
    for (; local_24 <= local_44; local_24 = local_24 + 1) {
      dVar2 = sc_la(this,local_24,local_48);
      local_2c[local_20][local_48] = dVar2;
      local_20 = local_20 + 1;
    }
  }
  local_14 = vector(1,local_30);
  for (local_24 = 1; local_24 < *param_1; local_24 = local_24 + 1) {
    local_14[local_24] = *(float *)(*(int *)(this + 0x300) + local_24 * 4);
  }
  local_20 = local_24;
  for (local_34 = 0; local_34 < param_5; local_34 = local_34 + 1) {
    local_7c = param_2[local_34];
    local_78 = local_7c + param_3[local_34];
    for (local_40 = 0; local_40 <= local_7c; local_40 = local_40 + 1) {
      local_28[local_40] = *(float *)(*(int *)(this + 0x300) + local_24 * 4);
      local_24 = local_24 + 1;
    }
    local_24 = local_24 + -1;
    if (local_78 != local_7c) {
      LMConvert::LMConvert(local_a0,local_28,local_7c + 1,local_78,local_7c);
      local_8 = 1;
      for (local_40 = 0; local_40 < local_78; local_40 = local_40 + 1) {
        fVar1 = LMConvert::output(local_a0,local_40);
        local_28[local_40] = fVar1;
      }
      local_8 = 0xffffffff;
      LMConvert::~LMConvert(local_a0);
    }
    for (local_40 = 0; local_40 < local_78; local_40 = local_40 + 1) {
      local_14[local_20] = local_28[local_40];
      local_20 = local_20 + 1;
    }
  }
  for (; local_24 <= local_44; local_24 = local_24 + 1) {
    local_14[local_20] = *(float *)(*(int *)(this + 0x300) + local_24 * 4);
    local_20 = local_20 + 1;
  }
  pm(this,local_2c,local_14,local_30,1,local_30);
  envelope(this,local_3c);
  free_vector(local_28,1,local_44);
  ExceptionList = local_10;
  return;
}

//===== 0x1001daec =====

void FUN_1001daec(void)

{
  FUN_1001daf6();
  return;
}

//===== 0x1001daf6 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1001daf6(void)

{
  _DAT_10042118 = acos(-1.0);
  return;
}

//===== 0x1001db10 =====

/* Library Function - Single Match
    public: __thiscall CCmdUI::CCmdUI(void)
   
   Libraries: Visual Studio 2003 Debug, Visual Studio 2005 Debug, Visual Studio 2008 Debug, Visual
   Studio 2010 Debug */

CCmdUI * __thiscall CCmdUI::CCmdUI(CCmdUI *this)

{
  *(undefined4 *)this = 1;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x1c) = 0;
  *(undefined4 *)(this + 0x20) = 0;
  *(undefined4 *)(this + 0x24) = 0;
  return this;
}

//===== 0x1001db81 =====

undefined4 * __thiscall FUN_1001db81(void *this,undefined4 *param_1)

{
  *(undefined4 *)this = 1;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0xc) = 0;
  *(undefined4 *)((int)this + 0x10) = 0;
  *(undefined4 *)((int)this + 0x14) = 0;
  *(undefined4 *)((int)this + 0x18) = 0;
  *(undefined4 *)((int)this + 0x1c) = 0;
  *(undefined4 *)((int)this + 0x20) = 0;
  *(undefined4 *)((int)this + 0x24) = 0;
  FUN_1001dc00(this,param_1);
  return this;
}

//===== 0x1001dc00 =====

undefined4 * __thiscall FUN_1001dc00(void *this,undefined4 *param_1)

{
  int *piVar1;
  int local_8;
  
  if (param_1 != this) {
    FUN_1001ddd8((int)this);
    *(undefined4 *)((int)this + 0x18) = param_1[6];
    *(undefined4 *)((int)this + 0x1c) = param_1[7];
    *(undefined4 *)((int)this + 0x20) = param_1[8];
    *(undefined4 *)((int)this + 0x24) = param_1[9];
    piVar1 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 4) = piVar1;
    piVar1 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 0x10) = piVar1;
    piVar1 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 0x14) = piVar1;
    piVar1 = ivector(1,*(long *)((int)this + 0x1c));
    *(int **)((int)this + 8) = piVar1;
    piVar1 = ivector(1,*(long *)((int)this + 0x1c));
    *(int **)((int)this + 0xc) = piVar1;
    if ((((*(int *)((int)this + 4) == 0) || (*(int *)((int)this + 8) == 0)) ||
        (*(int *)((int)this + 0xc) == 0)) ||
       ((*(int *)((int)this + 0x10) == 0 || (*(int *)((int)this + 0x14) == 0)))) {
      *(undefined4 *)this = 2;
      FUN_1001ddd8((int)this);
    }
    else {
      for (local_8 = 1; local_8 <= *(int *)((int)this + 0x18); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)((int)this + 4) + local_8 * 4) =
             *(undefined4 *)(param_1[1] + local_8 * 4);
        *(undefined4 *)(*(int *)((int)this + 0x10) + local_8 * 4) =
             *(undefined4 *)(param_1[4] + local_8 * 4);
        *(undefined4 *)(*(int *)((int)this + 8) + local_8 * 4) =
             *(undefined4 *)(param_1[2] + local_8 * 4);
        *(undefined4 *)(*(int *)((int)this + 0xc) + local_8 * 4) =
             *(undefined4 *)(param_1[3] + local_8 * 4);
        *(undefined4 *)(*(int *)((int)this + 0x14) + local_8 * 4) =
             *(undefined4 *)(param_1[5] + local_8 * 4);
      }
      *(undefined4 *)(*(int *)((int)this + 8) + local_8 * 4) =
           *(undefined4 *)(param_1[2] + local_8 * 4);
      *(undefined4 *)(*(int *)((int)this + 0xc) + local_8 * 4) =
           *(undefined4 *)(param_1[3] + local_8 * 4);
    }
  }
  return this;
}

//===== 0x1001ddd8 =====

void __fastcall FUN_1001ddd8(int param_1)

{
  if (*(int *)(param_1 + 4) != 0) {
    free_ivector(*(int **)(param_1 + 4),1,*(long *)(param_1 + 0x18));
    *(undefined4 *)(param_1 + 4) = 0;
  }
  if (*(int *)(param_1 + 0x10) != 0) {
    free_ivector(*(int **)(param_1 + 0x10),1,*(long *)(param_1 + 0x18));
    *(undefined4 *)(param_1 + 0x10) = 0;
  }
  if (*(int *)(param_1 + 0x14) != 0) {
    free_ivector(*(int **)(param_1 + 0x14),1,*(long *)(param_1 + 0x18));
    *(undefined4 *)(param_1 + 0x14) = 0;
  }
  if (*(int *)(param_1 + 8) != 0) {
    free_ivector(*(int **)(param_1 + 8),1,*(long *)(param_1 + 0x1c));
    *(undefined4 *)(param_1 + 8) = 0;
  }
  if (*(int *)(param_1 + 0xc) != 0) {
    free_ivector(*(int **)(param_1 + 0xc),1,*(long *)(param_1 + 0x1c));
    *(undefined4 *)(param_1 + 0xc) = 0;
  }
  *(undefined4 *)(param_1 + 0x1c) = 0;
  *(undefined4 *)(param_1 + 0x18) = 0;
  return;
}

//===== 0x1001dece =====

void __fastcall FUN_1001dece(int param_1)

{
  FUN_1001ddd8(param_1);
  return;
}

//===== 0x1001dee1 =====

undefined4 __thiscall
FUN_1001dee1(void *this,int param_1,int param_2,int param_3,int param_4,int param_5)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  int *piVar5;
  int *piVar6;
  int *piVar7;
  int iVar8;
  int local_38;
  int local_20;
  int local_1c;
  int local_8;
  
  FUN_1001ddd8((int)this);
  local_20 = 1;
  iVar8 = *(int *)(param_1 + 4);
  iVar1 = *(int *)(param_1 + param_2 * 4);
  local_1c = 1;
  iVar2 = *(int *)(param_3 + 4);
  iVar3 = *(int *)(param_3 + param_4 * 4);
  if (iVar8 < iVar2) {
    local_20 = 2;
  }
  if (iVar3 < iVar1) {
    param_2 = param_2 + -1;
  }
  *(int *)((int)this + 0x18) = (param_2 - local_20) + 1;
  *(int *)((int)this + 0x1c) = param_4;
  if ((*(int *)((int)this + 0x1c) < 2) ||
     (*(int *)((int)this + 0x1c) != *(int *)((int)this + 0x18) + 1)) {
    fprintf((FILE *)(_iob_exref + 0x40),s_PKDET__set__Np__d__Nt__d__Nt_sho_10040344,
            *(undefined4 *)((int)this + 0x18),*(undefined4 *)((int)this + 0x1c));
    fprintf((FILE *)(_iob_exref + 0x40),s_px1__d_tx1__d_pxn__d_txn__d_10040374,iVar8,iVar2,iVar1,
            iVar3);
    *(undefined4 *)((int)this + 0x18) = 0;
    *(undefined4 *)((int)this + 0x1c) = 0;
    uVar4 = 0;
  }
  else {
    piVar5 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 4) = piVar5;
    piVar5 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 0x10) = piVar5;
    piVar5 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 0x14) = piVar5;
    piVar5 = ivector(1,*(long *)((int)this + 0x18));
    piVar6 = ivector(1,*(int *)((int)this + 0x18) + -1);
    piVar7 = ivector(1,*(long *)((int)this + 0x1c));
    *(int **)((int)this + 8) = piVar7;
    piVar7 = ivector(1,*(long *)((int)this + 0x1c));
    *(int **)((int)this + 0xc) = piVar7;
    if (((*(int *)((int)this + 4) == 0) ||
        (((*(int *)((int)this + 8) == 0 || (*(int *)((int)this + 0xc) == 0)) ||
         (*(int *)((int)this + 0x10) == 0)))) ||
       (((*(int *)((int)this + 0x14) == 0 || (piVar6 == (int *)0x0)) || (piVar5 == (int *)0x0)))) {
      *(undefined4 *)this = 2;
      *(undefined4 *)((int)this + 0x18) = 0;
      *(undefined4 *)((int)this + 0x1c) = 0;
      uVar4 = 0;
    }
    else {
      for (local_8 = 1; local_8 <= *(int *)((int)this + 0x18); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)((int)this + 4) + local_8 * 4) =
             *(undefined4 *)(param_1 + local_20 * 4);
        *(undefined4 *)(*(int *)((int)this + 8) + local_8 * 4) =
             *(undefined4 *)(param_3 + local_1c * 4);
        local_1c = local_1c + 1;
        *(undefined4 *)(*(int *)((int)this + 0x10) + local_8 * 4) =
             *(undefined4 *)(param_5 + local_20 * 4);
        piVar5[local_8] = *(int *)(*(int *)((int)this + 0x10) + local_8 * 4);
        local_20 = local_20 + 1;
        *(undefined4 *)(*(int *)((int)this + 0x14) + local_8 * 4) = 0;
        if (local_8 < *(int *)((int)this + 0x18)) {
          *(int *)(*(int *)((int)this + 0xc) + 4 + local_8 * 4) =
               *(int *)(param_1 + local_20 * 4) - *(int *)(param_1 + -4 + local_20 * 4);
          piVar6[local_8] = *(int *)(*(int *)((int)this + 0xc) + 4 + local_8 * 4);
        }
      }
      *(undefined4 *)(*(int *)((int)this + 8) + local_8 * 4) =
           *(undefined4 *)(param_3 + local_1c * 4);
      qsort(piVar6 + 1,*(int *)((int)this + 0x18) - 1,4,FUN_1001e33f);
      if ((*(int *)((int)this + 0x18) - 1U & 1) == 0) {
        iVar8 = (*(int *)((int)this + 0x18) + -1) / 2;
        *(int *)((int)this + 0x20) = (piVar6[iVar8] + piVar6[iVar8 + 1]) / 2;
      }
      else {
        *(int *)((int)this + 0x20) = piVar6[(*(int *)((int)this + 0x18) + -1) / 2 + 1];
      }
      *(undefined4 *)(*(int *)((int)this + 0xc) + *(int *)((int)this + 0x1c) * 4) =
           *(undefined4 *)((int)this + 0x20);
      *(undefined4 *)(*(int *)((int)this + 0xc) + 4) =
           *(undefined4 *)(*(int *)((int)this + 0xc) + *(int *)((int)this + 0x1c) * 4);
      free_ivector(piVar6,1,*(int *)((int)this + 0x18) + -1);
      qsort(piVar5 + 1,*(size_t *)((int)this + 0x18),4,FUN_1001e33f);
      if ((*(uint *)((int)this + 0x18) & 1) == 0) {
        local_38 = (piVar5[*(int *)((int)this + 0x18) / 2] +
                   piVar5[*(int *)((int)this + 0x18) / 2 + 1]) / 2;
      }
      else {
        local_38 = piVar5[*(int *)((int)this + 0x18) / 2 + 1];
      }
      *(int *)((int)this + 0x24) = local_38;
      free_ivector(piVar5,1,*(long *)((int)this + 0x18));
      uVar4 = 1;
    }
  }
  return uVar4;
}

//===== 0x1001e33f =====

int __cdecl FUN_1001e33f(int *param_1,int *param_2)

{
  return *param_1 - *param_2;
}

//===== 0x1001e34e =====

undefined4 __thiscall FUN_1001e34e(void *this,int param_1,int param_2)

{
  undefined4 uVar1;
  int *piVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  undefined4 *puVar7;
  SW *pSVar8;
  Wvfm *pWVar9;
  int local_54;
  SW local_44 [20];
  Wvfm local_30 [20];
  int *local_1c;
  int *local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_100370f2;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  FUN_1001ddd8((int)this);
  *(int *)((int)this + 0x18) = param_2;
  *(int *)((int)this + 0x1c) = param_2 + 1;
  if (*(int *)((int)this + 0x1c) < 2) {
    fprintf((FILE *)(_iob_exref + 0x40),s_PKDET__set__Np__d__Nt__d__Nt__Np_10040394,
            *(undefined4 *)((int)this + 0x18),*(undefined4 *)((int)this + 0x1c));
    *(undefined4 *)((int)this + 0x18) = 0;
    *(undefined4 *)((int)this + 0x1c) = 0;
    uVar1 = 0;
  }
  else {
    piVar2 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 4) = piVar2;
    piVar2 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 0x10) = piVar2;
    piVar2 = ivector(1,*(long *)((int)this + 0x18));
    *(int **)((int)this + 0x14) = piVar2;
    piVar2 = ivector(1,*(long *)((int)this + 0x1c));
    *(int **)((int)this + 8) = piVar2;
    piVar2 = ivector(1,*(long *)((int)this + 0x1c));
    *(int **)((int)this + 0xc) = piVar2;
    local_18 = ivector(1,*(long *)((int)this + 0x18));
    local_1c = ivector(1,*(int *)((int)this + 0x18) + -1);
    if ((((*(int *)((int)this + 4) == 0) || (*(int *)((int)this + 8) == 0)) ||
        (*(int *)((int)this + 0xc) == 0)) ||
       (((*(int *)((int)this + 0x10) == 0 || (*(int *)((int)this + 0x14) == 0)) ||
        ((local_1c == (int *)0x0 || (local_18 == (int *)0x0)))))) {
      *(undefined4 *)this = 2;
      *(undefined4 *)((int)this + 0x18) = 0;
      *(undefined4 *)((int)this + 0x1c) = 0;
      uVar1 = 0;
    }
    else {
      for (local_14 = 1; local_14 < param_2; local_14 = local_14 + 1) {
        puVar7 = (undefined4 *)(param_1 + local_14 * 0x14);
        pSVar8 = local_44;
        for (iVar6 = 5; iVar6 != 0; iVar6 = iVar6 + -1) {
          *(undefined4 *)pSVar8 = *puVar7;
          puVar7 = puVar7 + 1;
          pSVar8 = pSVar8 + 4;
        }
        local_8 = 0;
        puVar7 = (undefined4 *)(param_1 + (local_14 + 1) * 0x14);
        pWVar9 = local_30;
        for (iVar6 = 5; iVar6 != 0; iVar6 = iVar6 + -1) {
          *(undefined4 *)pWVar9 = *puVar7;
          puVar7 = puVar7 + 1;
          pWVar9 = pWVar9 + 4;
        }
        local_8 = CONCAT31(local_8._1_3_,1);
        iVar6 = SW::alignedLength(local_44);
        iVar3 = Wvfm::annotate(local_30);
        if (iVar6 != iVar3) {
          iVar6 = SW::alignedLength(local_44);
          iVar3 = Wvfm::annotate((Wvfm *)local_44);
          iVar4 = SW::alignedLength((SW *)local_30);
          iVar5 = Wvfm::annotate(local_30);
          if (iVar4 - iVar5 < iVar6 - iVar3) {
            iVar6 = Wvfm::annotate(local_30);
            BandStat::bbgn((BandStat *)(local_14 * 0x14 + param_1),iVar6);
          }
          else {
            iVar6 = SW::alignedLength(local_44);
            Wvfm::annotate((Wvfm *)(param_1 + (local_14 + 1) * 0x14),iVar6);
          }
        }
        iVar6 = Annotate::getNumCurrFix((Annotate *)(local_14 * 0x14 + param_1));
        *(int *)(*(int *)((int)this + 4) + local_14 * 4) = iVar6;
        iVar6 = Wvfm::annotate((Wvfm *)(param_1 + local_14 * 0x14));
        *(int *)(*(int *)((int)this + 8) + local_14 * 4) = iVar6;
        iVar6 = FUN_1001ea70((int *)(param_1 + local_14 * 0x14));
        *(int *)(*(int *)((int)this + 0x10) + local_14 * 4) = iVar6;
        local_18[local_14] = *(int *)(*(int *)((int)this + 0x10) + local_14 * 4);
        iVar6 = Annotate::getNumFwhmGapLen((Annotate *)(local_14 * 0x14 + param_1));
        *(int *)(*(int *)((int)this + 0x14) + local_14 * 4) = iVar6;
        iVar6 = Annotate::getNumCurrFix((Annotate *)(param_1 + (local_14 + 1) * 0x14));
        iVar3 = Annotate::getNumCurrFix((Annotate *)(param_1 + local_14 * 0x14));
        *(int *)(*(int *)((int)this + 0xc) + 4 + local_14 * 4) = iVar6 - iVar3;
        local_1c[local_14] = *(int *)(*(int *)((int)this + 0xc) + 4 + local_14 * 4);
        local_8 = local_8 & 0xffffff00;
        BandStat::~BandStat((BandStat *)local_30);
        local_8 = 0xffffffff;
        BandStat::~BandStat((BandStat *)local_44);
      }
      iVar6 = Annotate::getNumCurrFix((Annotate *)(param_1 + local_14 * 0x14));
      *(int *)(*(int *)((int)this + 4) + local_14 * 4) = iVar6;
      iVar6 = Wvfm::annotate((Wvfm *)(param_1 + local_14 * 0x14));
      *(int *)(*(int *)((int)this + 8) + local_14 * 4) = iVar6;
      iVar6 = SW::alignedLength((SW *)(param_1 + local_14 * 0x14));
      *(int *)(*(int *)((int)this + 8) + 4 + local_14 * 4) = iVar6;
      *(int *)(*(int *)((int)this + 0x10) + local_14 * 4) =
           *(int *)(*(int *)((int)this + 8) + 4 + local_14 * 4) -
           *(int *)(*(int *)((int)this + 8) + local_14 * 4);
      local_18[local_14] = *(int *)(*(int *)((int)this + 0x10) + local_14 * 4);
      iVar6 = Annotate::getNumFwhmGapLen((Annotate *)(local_14 * 0x14 + param_1));
      *(int *)(*(int *)((int)this + 0x14) + local_14 * 4) = iVar6;
      qsort(local_1c + 1,*(int *)((int)this + 0x18) - 1,4,FUN_1001e33f);
      if ((*(int *)((int)this + 0x18) - 1U & 1) == 0) {
        iVar6 = (*(int *)((int)this + 0x18) + -1) / 2;
        *(int *)((int)this + 0x20) = (local_1c[iVar6] + local_1c[iVar6 + 1]) / 2;
      }
      else {
        *(int *)((int)this + 0x20) = local_1c[(*(int *)((int)this + 0x18) + -1) / 2 + 1];
      }
      *(undefined4 *)(*(int *)((int)this + 0xc) + *(int *)((int)this + 0x1c) * 4) =
           *(undefined4 *)((int)this + 0x20);
      *(undefined4 *)(*(int *)((int)this + 0xc) + 4) =
           *(undefined4 *)(*(int *)((int)this + 0xc) + *(int *)((int)this + 0x1c) * 4);
      free_ivector(local_1c,1,*(int *)((int)this + 0x18) + -1);
      qsort(local_18 + 1,*(size_t *)((int)this + 0x18),4,FUN_1001e33f);
      if ((*(uint *)((int)this + 0x18) & 1) == 0) {
        local_54 = (local_18[*(int *)((int)this + 0x18) / 2] +
                   local_18[*(int *)((int)this + 0x18) / 2 + 1]) / 2;
      }
      else {
        local_54 = local_18[*(int *)((int)this + 0x18) / 2 + 1];
      }
      *(int *)((int)this + 0x24) = local_54;
      free_ivector(local_18,1,*(long *)((int)this + 0x18));
      uVar1 = 1;
    }
  }
  ExceptionList = local_10;
  return uVar1;
}

//===== 0x1001e8a8 =====

void __fastcall FUN_1001e8a8(int param_1)

{
  int local_8;
  
  printf(s_PKDET__debug_100403b8);
  printf(s_Np__3d_Nt__3d_medGap__2d_medWid__100403c8,*(undefined4 *)(param_1 + 0x18),
         *(undefined4 *)(param_1 + 0x1c),*(undefined4 *)(param_1 + 0x20),
         *(undefined4 *)(param_1 + 0x24));
  if (*(int *)(param_1 + 8) == 0) {
    printf(s_PKDET__debug_failed__ptr___p_100403f4,*(undefined4 *)(param_1 + 8));
  }
  else if (*(int *)(param_1 + 4) == 0) {
    printf(s_PKDET__debug_failed__ppk___p_10040414,*(undefined4 *)(param_1 + 4));
  }
  else if (*(int *)(param_1 + 0xc) == 0) {
    printf(s_PKDET__debug_failed__gap___p_10040434,*(undefined4 *)(param_1 + 0xc));
  }
  else if (*(int *)(param_1 + 0x10) == 0) {
    printf(s_PKDET__debug_failed__wid___p_10040454,*(undefined4 *)(param_1 + 0x10));
  }
  else if (*(int *)(param_1 + 0x14) == 0) {
    printf(s_PKDET__debug_failed__ins___p_10040474,*(undefined4 *)(param_1 + 0x14));
  }
  else {
    for (local_8 = 1; local_8 <= *(int *)(param_1 + 0x18); local_8 = local_8 + 1) {
      printf(s__3d___4d__4d__4d__lgap__2d_rgap__10040494,local_8,
             *(undefined4 *)(*(int *)(param_1 + 8) + local_8 * 4),
             *(undefined4 *)(*(int *)(param_1 + 4) + local_8 * 4),
             *(undefined4 *)(*(int *)(param_1 + 8) + 4 + local_8 * 4),
             *(undefined4 *)(*(int *)(param_1 + 0xc) + local_8 * 4),
             *(undefined4 *)(*(int *)(param_1 + 0xc) + 4 + local_8 * 4),
             *(undefined4 *)(*(int *)(param_1 + 0x10) + local_8 * 4),
             *(undefined4 *)(*(int *)(param_1 + 0x14) + local_8 * 4));
      fflush((FILE *)(_iob_exref + 0x20));
    }
  }
  return;
}

//===== 0x1001ea46 =====

void FUN_1001ea46(void)

{
  FUN_1001ea50();
  return;
}

//===== 0x1001ea50 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1001ea50(void)

{
  _DAT_10042180 = acos(-1.0);
  return;
}

//===== 0x1001ea70 =====

int __fastcall FUN_1001ea70(int *param_1)

{
  return (param_1[2] - *param_1) + 1;
}

//===== 0x1001ea90 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Wvfm::noZeros(void) */

void __thiscall Wvfm::noZeros(Wvfm *this)

{
  int iVar1;
  int local_c;
  int local_8;
  
                    /* 0x1ea90  284  ?noZeros@Wvfm@@AAEXXZ */
  local_8 = 1;
  while( true ) {
    iVar1 = cols(this);
    if (iVar1 < local_8) break;
    local_c = bgni(this);
    while( true ) {
      iVar1 = endi(this);
      if (iVar1 < local_c) break;
      if (_DAT_10038b38 == *(double *)(*(int *)(*(int *)(this + 0xc4) + local_c * 4) + local_8 * 8))
      {
        iVar1 = *(int *)(*(int *)(this + 0xc4) + local_c * 4);
        *(undefined4 *)(iVar1 + local_8 * 8) = 0;
        *(undefined4 *)(iVar1 + 4 + local_8 * 8) = 0x3cb00000;
      }
      local_c = local_c + 1;
    }
    local_8 = local_8 + 1;
  }
  return;
}

//===== 0x1001eb26 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Wvfm::fixCurrentSag(long &,long,long,float) */

void __thiscall
Wvfm::fixCurrentSag(Wvfm *this,long *param_1,long param_2,long param_3,float param_4)

{
  int iVar1;
  int iVar2;
  float fVar3;
  int local_ac;
  LMConvert local_a8 [36];
  float *local_84;
  float local_80;
  int aiStack_7c [4];
  long local_6c;
  int aiStack_68 [5];
  int local_54;
  int aiStack_50 [5];
  float local_3c;
  long local_38;
  int aiStack_34 [4];
  int local_24;
  int local_20;
  int local_1c;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x1eb26  161  ?fixCurrentSag@Wvfm@@AAEXAAJJJM@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003710c;
  local_10 = ExceptionList;
  local_54 = (param_3 - param_2) + 1;
  local_18 = 0;
  local_38 = param_2;
  local_6c = param_3;
  for (local_24 = 0; local_24 < 4; local_24 = local_24 + 1) {
    aiStack_7c[local_24] = aiStack_34[local_24 + -1] + ((param_3 - param_2) + 1) / 5;
    aiStack_34[local_24] = aiStack_7c[local_24] + 1;
  }
  ExceptionList = &local_10;
  for (local_24 = 0; local_24 < 5; local_24 = local_24 + 1) {
    local_80 = 0.0;
    for (local_1c = aiStack_34[local_24 + -1]; local_1c <= aiStack_7c[local_24];
        local_1c = local_1c + 1) {
      local_80 = local_80 + *(float *)(*(int *)(this + 0x300) + local_1c * 4);
    }
    iVar2 = ftol();
    aiStack_50[local_24] = iVar2;
    aiStack_68[local_24] = (aiStack_7c[local_24] - aiStack_34[local_24 + -1]) + 1;
    local_18 = local_18 + aiStack_50[local_24];
  }
  local_3c = (float)local_18 / (float)local_54;
  if ((float)local_18 / (float)local_54 < _DAT_10038b44) {
    for (local_24 = 0; local_24 < 5; local_24 = local_24 + 1) {
      if (*(int *)this != 0) {
        Annotate::recordCurrFix
                  ((Annotate *)(this + 4),aiStack_34[local_24 + -1],aiStack_7c[local_24],
                   aiStack_50[local_24],aiStack_68[local_24]);
      }
      for (local_14 = 1; local_14 <= aiStack_50[local_24]; local_14 = local_14 + 1) {
        *(float *)(*(int *)(this + 0x300) + -4 + (*param_1 + local_14) * 4) = param_4;
      }
      local_84 = vector(1,aiStack_68[local_24] + 1);
      for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
        local_ac = 1;
        for (local_14 = aiStack_34[local_24 + -1]; local_14 <= aiStack_7c[local_24];
            local_14 = local_14 + 1) {
          local_84[local_ac] =
               (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + local_14 * 4) + local_20 * 8);
          local_ac = local_ac + 1;
        }
        local_84[local_ac] =
             (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + -4 + local_14 * 4) + local_20 * 8);
        LMConvert::LMConvert
                  (local_a8,local_84 + 1,aiStack_68[local_24] + 1,aiStack_50[local_24],
                   aiStack_68[local_24]);
        local_8 = 0;
        for (local_14 = 1; local_14 <= aiStack_50[local_24]; local_14 = local_14 + 1) {
          fVar3 = LMConvert::output(local_a8,local_14 + -1);
          *(double *)
           (*(int *)(*(int *)(this + 0xc4) + -4 + (*param_1 + local_14) * 4) + local_20 * 8) =
               (double)fVar3;
        }
        local_8 = 0xffffffff;
        LMConvert::~LMConvert(local_a8);
      }
      free_vector(local_84,1,aiStack_68[local_24] + 1);
      *param_1 = *param_1 + aiStack_50[local_24];
    }
  }
  else {
    for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
      for (local_14 = param_2; local_14 <= param_3; local_14 = local_14 + 1) {
        iVar2 = *(int *)(*(int *)(this + 0xc4) + local_14 * 4);
        iVar1 = *(int *)(*(int *)(this + 0xc4) + ((*param_1 + local_14) - param_2) * 4);
        *(undefined4 *)(iVar1 + local_20 * 8) = *(undefined4 *)(iVar2 + local_20 * 8);
        *(undefined4 *)(iVar1 + 4 + local_20 * 8) = *(undefined4 *)(iVar2 + 4 + local_20 * 8);
      }
    }
    *param_1 = *param_1 + local_54;
  }
  ExceptionList = local_10;
  return;
}

//===== 0x1001ef20 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: int __thiscall Wvfm::fixCurrent(void) */

int __thiscall Wvfm::fixCurrent(Wvfm *this)

{
  int iVar1;
  float fVar2;
  int iVar3;
  float local_17c;
  float local_178;
  float local_174;
  float local_170;
  float local_16c;
  int local_160;
  int local_14c;
  float local_13c;
  float local_138;
  float local_134;
  float local_130;
  int aiStack_128 [2];
  float afStack_120 [43];
  float local_74;
  float local_70 [4];
  float local_60;
  float *local_5c;
  double local_58;
  int local_50;
  int local_4c;
  int local_48;
  int local_44;
  float local_40;
  float local_3c;
  int local_38;
  long local_34;
  int local_30;
  float local_2c;
  int local_28;
  int local_24;
  int local_20;
  int local_1c;
  float local_18;
  float *local_14;
  size_t local_10;
  float local_c;
  int local_8;
  
                    /* 0x1ef20  160  ?fixCurrent@Wvfm@@AAEHXZ */
  local_10 = rows(this);
  local_14 = vector(1,local_10);
  local_c = 0.0;
  local_1c = 0;
  for (local_20 = 1; local_20 <= (int)local_10; local_20 = local_20 + 1) {
    local_14[local_20] = *(float *)(*(int *)(this + 0x300) + local_20 * 4);
    if ((local_20 < 100) && (local_c < *(float *)(*(int *)(this + 0x300) + local_20 * 4))) {
      local_1c = local_20;
      local_c = *(float *)(*(int *)(this + 0x300) + local_20 * 4);
    }
  }
  local_18 = local_c;
  local_8 = local_1c;
  local_20 = local_1c;
  while (local_20 = local_20 + 1, local_20 <= (int)local_10) {
    if (*(float *)(*(int *)(this + 0x300) + local_20 * 4) < local_18) {
      local_8 = local_20;
      local_18 = *(float *)(*(int *)(this + 0x300) + local_20 * 4);
    }
  }
  if (local_1c == 0) {
    free_vector(local_14,1,local_10);
    iVar3 = 0xa2;
  }
  else {
    local_5c = (float *)0x0;
    local_50 = (int)(local_10 * 3 + ((int)(local_10 * 3) >> 0x1f & 3U)) >> 2;
    qsort(local_14 + 1,local_10,4,FUN_1001f8c9);
    local_2c = local_14[local_10 - local_50];
    local_5c = vector(1,local_10);
    local_24 = 1;
    for (local_20 = local_1c; local_20 <= (int)local_10; local_20 = local_20 + 1) {
      if (local_2c <= *(float *)(*(int *)(this + 0x300) + local_20 * 4)) {
        local_14[local_24] = (float)local_20;
        local_5c[local_24] = *(float *)(*(int *)(this + 0x300) + local_20 * 4);
        local_24 = local_24 + 1;
      }
    }
    local_24 = local_24 + -1;
    polfit(local_14,local_5c,(float *)0x0,local_24,3,0,local_70,&local_40);
    free_vector(local_14,1,local_10);
    free_vector(local_5c,1,local_10);
    local_3c = local_18;
    local_60 = local_c;
    if (_DAT_10038b48 == local_70[3]) {
      if (_DAT_10038b48 < local_70[2]) {
        return 0xe7;
      }
      local_17c = (float)(int)local_10 * local_70[2] + local_70[1];
      local_178 = local_17c;
      if (local_17c < local_70[1]) {
        local_178 = local_70[1];
      }
      local_60 = local_178;
      if (local_70[1] < local_17c) {
        local_17c = local_70[1];
      }
      local_3c = local_17c;
    }
    else {
      fVar2 = -local_70[2] / (_DAT_10038b4c * local_70[3]);
      local_13c = (float)(int)local_10;
      local_138 = local_70[1];
      local_134 = local_70[1];
      local_130 = fVar2;
      for (local_20 = 2; local_20 < 4; local_20 = local_20 + 1) {
        local_138 = local_70[local_20] * local_130 + local_138;
        local_130 = local_130 * fVar2;
        local_134 = local_70[local_20] * local_13c + local_134;
        local_13c = (float)(int)local_10 * local_13c;
      }
      if (local_70[3] <= _DAT_10038b48) {
        if ((fVar2 < (float)local_1c) || ((float)(int)local_10 < fVar2)) {
          if (local_70[1] <= local_134) {
            local_170 = local_134;
          }
          else {
            local_170 = local_70[1];
          }
          local_60 = local_170;
        }
        else {
          local_60 = local_138;
        }
        if (local_134 <= local_70[1]) {
          local_174 = local_134;
        }
        else {
          local_174 = local_70[1];
        }
        local_3c = local_174;
      }
      else {
        if ((fVar2 < (float)local_1c) || ((float)(int)local_10 < fVar2)) {
          if (local_134 <= local_70[1]) {
            local_16c = local_134;
          }
          else {
            local_16c = local_70[1];
          }
          local_3c = local_16c;
        }
        else {
          local_3c = local_138;
        }
        if (local_70[1] < local_134) {
          return 0xd7;
        }
        local_60 = local_70[1];
      }
    }
    if ((((local_3c < _DAT_10038b50 * local_18) || (local_3c < _DAT_10038b48)) ||
        (_DAT_10038b54 * local_c < local_60)) || (_DAT_10038b58 <= local_40)) {
      iVar3 = 0xf5;
    }
    else {
      local_48 = 0;
      local_28 = local_1c;
      local_38 = local_1c;
      local_44 = 0;
      local_4c = 1;
      for (local_20 = local_1c; local_20 <= (int)local_10; local_20 = local_20 + 1) {
        fVar2 = (float)local_20;
        local_58 = (double)local_70[1];
        for (local_14c = 2; local_14c < 4; local_14c = local_14c + 1) {
          local_58 = (double)(local_70[local_14c] * fVar2 + (float)local_58);
          fVar2 = (float)local_20 * fVar2;
        }
        if (_DAT_10038b38 < local_58) {
          fVar2 = *(float *)(*(int *)(this + 0x300) + local_20 * 4) / (float)local_58;
          if (local_4c == 1) {
            if (_DAT_10038b30 <= fVar2) {
              if (0 < local_44) {
                local_44 = local_44 + -1;
              }
            }
            else {
              local_44 = local_44 + 1;
              if (0x2c < local_44) {
                local_74 = (float)local_58;
                local_4c = 0;
                local_28 = (local_20 - local_44) + 1;
                local_44 = 0;
              }
            }
          }
          else {
            local_38 = local_20;
            if (fVar2 < _DAT_10038b34) {
              if (0 < local_44) {
                local_44 = local_44 + -1;
              }
            }
            else {
              local_44 = local_44 + 1;
              if (0x2d < local_44) {
                local_4c = 1;
                aiStack_128[local_48 * 3] = local_28;
                aiStack_128[local_48 * 3 + 1] = (local_38 - local_44) + 1;
                afStack_120[local_48 * 3] = (local_74 + (float)local_58) / (float)_DAT_10038b60;
                local_48 = local_48 + 1;
                if (0xe < local_48) break;
                local_44 = 0;
              }
            }
          }
        }
      }
      if (local_4c == 0) {
        aiStack_128[local_48 * 3] = local_28;
        aiStack_128[local_48 * 3 + 1] = local_38;
        afStack_120[local_48 * 3] = (local_74 + (float)local_58) / (float)_DAT_10038b60;
        local_48 = local_48 + 1;
      }
      local_30 = 1;
      local_34 = 1;
      if (0 < local_48) {
        for (local_20 = 0; local_20 < local_48; local_20 = local_20 + 1) {
          for (; local_30 < aiStack_128[local_20 * 3]; local_30 = local_30 + 1) {
            *(undefined4 *)(*(int *)(this + 0x300) + local_34 * 4) =
                 *(undefined4 *)(*(int *)(this + 0x300) + local_30 * 4);
            for (local_160 = 1; local_160 < 5; local_160 = local_160 + 1) {
              iVar3 = *(int *)(*(int *)(this + 0xc4) + local_30 * 4);
              iVar1 = *(int *)(*(int *)(this + 0xc4) + local_34 * 4);
              *(undefined4 *)(iVar1 + local_160 * 8) = *(undefined4 *)(iVar3 + local_160 * 8);
              *(undefined4 *)(iVar1 + 4 + local_160 * 8) =
                   *(undefined4 *)(iVar3 + 4 + local_160 * 8);
            }
            local_34 = local_34 + 1;
          }
          fixCurrentSag(this,&local_34,aiStack_128[local_20 * 3],aiStack_128[local_20 * 3 + 1],
                        afStack_120[local_20 * 3]);
          local_30 = aiStack_128[local_20 * 3 + 1] + 1;
        }
        iVar3 = rows(this);
        if (local_30 < iVar3) {
          while (iVar3 = rows(this), local_30 <= iVar3) {
            *(undefined4 *)(*(int *)(this + 0x300) + local_34 * 4) =
                 *(undefined4 *)(*(int *)(this + 0x300) + local_30 * 4);
            for (local_160 = 1; local_160 < 5; local_160 = local_160 + 1) {
              iVar3 = *(int *)(*(int *)(this + 0xc4) + local_30 * 4);
              iVar1 = *(int *)(*(int *)(this + 0xc4) + local_34 * 4);
              *(undefined4 *)(iVar1 + local_160 * 8) = *(undefined4 *)(iVar3 + local_160 * 8);
              *(undefined4 *)(iVar1 + 4 + local_160 * 8) =
                   *(undefined4 *)(iVar3 + 4 + local_160 * 8);
            }
            local_30 = local_30 + 1;
            local_34 = local_34 + 1;
          }
        }
        *(long *)(this + 0xb0) = local_34 + -1;
        *(undefined4 *)(this + 0xbc) = *(undefined4 *)(this + 0xb0);
      }
      iVar3 = 0;
    }
  }
  return iVar3;
}

//===== 0x1001f8c9 =====

undefined4 __cdecl FUN_1001f8c9(float *param_1,float *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x1001f90b =====

void FUN_1001f90b(void)

{
  FUN_1001f915();
  return;
}

//===== 0x1001f915 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1001f915(void)

{
  _DAT_100421e8 = acos(-1.0);
  return;
}

//===== 0x1001f92f =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Wvfm::prbevington(void) */

void __thiscall Wvfm::prbevington(Wvfm *this)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 local_14;
  undefined4 uStack_10;
  int local_c;
  int local_8;
  
                    /* 0x1f92f  308  ?prbevington@Wvfm@@AAEXXZ */
  for (local_c = 1; local_c < 5; local_c = local_c + 1) {
    local_14 = *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 4) + local_c * 8);
    uStack_10 = *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 4) + 4 + local_c * 8);
    for (local_8 = 2; local_8 < *(int *)(this + 0xb0); local_8 = local_8 + 1) {
      iVar1 = *(int *)(*(int *)(this + 0xc4) + local_8 * 4);
      uVar2 = *(undefined4 *)(iVar1 + local_c * 8);
      uVar3 = *(undefined4 *)(iVar1 + 4 + local_c * 8);
      *(double *)(*(int *)(*(int *)(this + 0xc4) + local_8 * 4) + local_c * 8) =
           *(double *)(*(int *)(*(int *)(this + 0xc4) + local_8 * 4) + local_c * 8) / _DAT_10038b60
           + ((double)CONCAT44(uStack_10,local_14) +
             *(double *)(*(int *)(*(int *)(this + 0xc4) + 4 + local_8 * 4) + local_c * 8)) /
             _DAT_10038b68;
      local_14 = uVar2;
      uStack_10 = uVar3;
    }
  }
  return;
}

//===== 0x1001fa1e =====

/* private: int __thiscall Wvfm::mdynpre(struct TestOptions &) */

int __thiscall Wvfm::mdynpre(Wvfm *this,TestOptions *param_1)

{
  float *pfVar1;
  int iVar2;
  int iVar3;
  float *pfVar4;
  int iVar5;
  double dVar6;
  int local_78;
  float local_60;
  int local_5c;
  float *local_58;
  float *local_54;
  float *local_50;
  double **local_4c;
  int local_48;
  int local_44;
  float local_40;
  int local_3c;
  int local_38;
  int local_34;
  MobCtrlTbl *local_30;
  int local_2c;
  int local_28;
  int local_24;
  float local_20;
  int local_1c;
  float local_18;
  undefined4 local_14;
  undefined4 local_10;
  int local_c;
  int local_8;
  
                    /* 0x1fa1e  276  ?mdynpre@Wvfm@@AAEHAAUTestOptions@@@Z */
  if (*(int *)this != 0) {
    Annotate::setNScnl((Annotate *)(this + 4),0,*(int *)(this + 0xb0));
  }
  local_8 = fixCurrent(this);
  if (*(int *)this != 0) {
    Annotate::setNScnl((Annotate *)(this + 4),1,*(int *)(this + 0xb0));
    BandStat::bbgn((BandStat *)(this + 4),local_8);
  }
  ObsInpSpec::laneOrder((ObsInpSpec *)(this + 0x210),(char *)(this + 0xdc));
  iVar2 = rows(this);
  iVar3 = rows(this);
  ObsInpSpec::boundaries((ObsInpSpec *)(this + 0x210),1,iVar3,iVar2);
  iVar2 = bgnEnd(this,param_1);
  if (iVar2 == 1) {
    *(undefined4 *)(this + 0x2f8) = *(undefined4 *)(this + 0xb8);
    *(undefined4 *)(this + 0x2fc) = *(undefined4 *)(this + 0xbc);
    local_c = decimateP(this,1);
    if (local_c != 0) {
      local_10 = *(undefined4 *)(this + 0xb8);
      local_14 = *(undefined4 *)(this + 0xbc);
      *(undefined4 *)(this + 0xb8) = 1;
      iVar2 = rows(this);
      *(int *)(this + 0xbc) = iVar2;
      iVar2 = bgnEnd(this,param_1);
      if (iVar2 != 1) {
        *(undefined4 *)(this + 0xb8) = local_10;
        *(undefined4 *)(this + 0xbc) = local_14;
      }
      if (*(int *)(this + 0xbc) - *(int *)(this + 0xb8) < 0x801) {
        iVar2 = *(int *)(this + 0xb8);
        iVar3 = rows(this);
        if (iVar2 + 0x801 < iVar3) {
          local_78 = *(int *)(this + 0xb8) + 0x801;
        }
        else {
          local_78 = rows(this);
        }
        *(int *)(this + 0xbc) = local_78;
      }
      decimateP(this,0);
    }
    if (*(int *)(this + 0x1b0) == 0) {
      *(undefined4 *)(this + 0x168) = 10;
      iVar2 = 0;
    }
    else {
      if (*(int *)this != 0) {
        Annotate::setNScnl((Annotate *)(this + 4),2,*(int *)(this + 0xb0));
        iVar2 = cols(this);
        iVar3 = rows(this);
        Annotate::setMtrxDim((Annotate *)(this + 4),iVar3,iVar2);
        Annotate::setTraces((Annotate *)(this + 4),0,*(double ***)(this + 0xc4));
        Annotate::setCurrent((Annotate *)(this + 4),*(float **)(this + 0x300));
        ObsInpSpec::measRange((ObsInpSpec *)(this + 0x210),&local_24,&local_1c,&local_28);
        ObsInpSpec::widthStats((ObsInpSpec *)(this + 0x210),&local_18,&local_20);
        Annotate::setDecimData((Annotate *)(this + 4),local_24,local_1c,local_28,local_18,local_20);
      }
      iVar2 = rows(this);
      ObsInpSpec::lmBoundaries
                ((ObsInpSpec *)(this + 0x210),*(int *)(this + 0xb8),*(int *)(this + 0xbc),iVar2);
      if ((*(uint *)param_1 >> 1 & 1) != 0) {
        prbevington(this);
      }
      iVar2 = specSep(this,param_1);
      if (iVar2 == 1) {
        if ((*(uint *)param_1 >> 5 & 1) != 0) {
          local_30 = (MobCtrlTbl *)0x0;
          local_2c = 0;
          local_30 = (MobCtrlTbl *)
                     FUN_10010270(*(int *)(this + 0xc4) + -4 + *(int *)(this + 0xb8) * 4,
                                  (*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1,&local_2c);
          if (local_30 == (MobCtrlTbl *)0x0) {
            *(uint *)param_1 = *(uint *)param_1 & 0xffffffdf;
          }
          else {
            FUN_10010d6d(*(int *)(this + 0xc4) + -4 + *(int *)(this + 0xb8) * 4,
                         (*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1,(int)local_30,local_2c)
            ;
            if (*(int *)this != 0) {
              Annotate::setMobTbl((Annotate *)(this + 4),local_30,local_2c);
            }
            operator_delete(local_30);
          }
        }
        if ((((*(int *)(this + 0xc0) != 5) && (local_c == 0)) && (*(int *)(this + 0x1b0) < 8)) &&
           (*(int *)(this + 0x16c) != 2)) {
          iVar2 = 3 - (uint)(*(int *)(this + 0x16c) != 0);
          ObsInpSpec::rateChgAction((ObsInpSpec *)(this + 0x210),2,iVar2);
          iVar3 = rows(this);
          local_34 = (iVar3 + 1) / iVar2;
          iVar5 = local_34 * iVar2 * iVar2 + 1;
          iVar3 = cols(this);
          local_4c = dmatrix(1,iVar5,1,iVar3);
          if (local_4c == (double **)0x0) {
            *(undefined4 *)(this + 0x168) = 2;
            return 0;
          }
          local_54 = vector(1,4);
          local_58 = vector(1,4);
          pfVar4 = vector(1,4);
          if (((local_54 == (float *)0x0) || (local_58 == (float *)0x0)) || (pfVar4 == (float *)0x0)
             ) {
            *(undefined4 *)(this + 0x168) = 2;
            return 0;
          }
          local_44 = 1;
          while (iVar3 = cols(this), local_44 <= iVar3) {
            iVar3 = bgni(this);
            local_38 = (iVar3 + -1) * iVar2 + 1;
            local_3c = bgni(this);
            while (iVar3 = endi(this), local_3c <= iVar3 + -3) {
              for (local_48 = 0; local_48 < 4; local_48 = local_48 + 1) {
                local_54[local_48 + 1] = (float)(local_3c + local_48);
                local_58[local_48 + 1] =
                     (float)*(double *)
                             (*(int *)(*(int *)(this + 0xc4) + (local_3c + local_48) * 4) +
                             local_44 * 8);
              }
              spline(local_54,local_58,4,local_58[2] - local_58[1],local_58[4] - local_58[3],pfVar4)
              ;
              for (local_48 = 0; local_48 < iVar2; local_48 = local_48 + 1) {
                for (local_5c = 0; local_5c < iVar2; local_5c = local_5c + 1) {
                  local_40 = (float)local_5c / (float)iVar2 + (float)(local_3c + local_48);
                  splint(local_54,local_58,pfVar4,4,local_40,&local_60);
                  dVar6 = floor((double)local_60);
                  local_4c[local_38][local_44] = dVar6;
                  local_38 = local_38 + 1;
                }
              }
              local_3c = local_3c + iVar2;
            }
            local_4c[local_38][local_44] = (double)local_58[4];
            local_44 = local_44 + 1;
          }
          local_50 = vector(1,iVar5);
          if (local_50 == (float *)0x0) {
            *(undefined4 *)(this + 0x168) = 2;
            return 0;
          }
          iVar3 = bgni(this);
          local_38 = (iVar3 + -1) * iVar2 + 1;
          local_3c = bgni(this);
          while (iVar3 = endi(this), local_3c <= iVar3 + -3) {
            for (local_48 = 0; local_48 < 4; local_48 = local_48 + 1) {
              local_54[local_48 + 1] = (float)(local_3c + local_48);
              local_58[local_48 + 1] =
                   *(float *)(*(int *)(this + 0x300) + (local_3c + local_48) * 4);
            }
            spline(local_54,local_58,4,local_58[2] - local_58[1],local_58[4] - local_58[3],pfVar4);
            for (local_48 = 0; local_48 < iVar2; local_48 = local_48 + 1) {
              for (local_5c = 0; local_5c < iVar2; local_5c = local_5c + 1) {
                local_40 = (float)local_5c / (float)iVar2 + (float)(local_3c + local_48);
                pfVar1 = local_50 + local_38;
                local_38 = local_38 + 1;
                splint(local_54,local_58,pfVar4,4,local_40,pfVar1);
              }
            }
            local_3c = local_3c + iVar2;
          }
          local_50[local_38] = pfVar4[4];
          free_vector(local_54,1,4);
          free_vector(local_58,1,4);
          free_vector(pfVar4,1,4);
          iVar3 = endi(this);
          iVar3 = (iVar3 * iVar2 - iVar2) + 1;
          iVar5 = bgni(this);
          pm(this,local_4c,local_50,local_38,(iVar5 * iVar2 - iVar2) + 1,iVar3);
          if (*(int *)this != 0) {
            Annotate::setNScnl((Annotate *)(this + 4),3,*(int *)(this + 0xb0));
          }
        }
        iVar2 = rows(this);
        ObsInpSpec::lmBoundaries
                  ((ObsInpSpec *)(this + 0x210),*(int *)(this + 0xb8),*(int *)(this + 0xbc),iVar2);
        iVar2 = 1;
      }
      else {
        iVar2 = 0;
      }
    }
  }
  else {
    iVar2 = 0;
  }
  return iVar2;
}

//===== 0x100202f3 =====

/* private: int __thiscall Wvfm::preproc(struct TestOptions &) */

int __thiscall Wvfm::preproc(Wvfm *this,TestOptions *param_1)

{
  int iVar1;
  int iVar2;
  
                    /* 0x202f3  309  ?preproc@Wvfm@@AAEHAAUTestOptions@@@Z */
  iVar1 = mdynpre(this,param_1);
  if (iVar1 == 1) {
    noZeros(this);
    *(int *)(this + 0xb8) = *(int *)(this + 0xb8) + 1;
    *(int *)(this + 0xbc) = *(int *)(this + 0xbc) + -1;
    iVar2 = rows(this);
    ObsInpSpec::lmBoundaries
              ((ObsInpSpec *)(this + 0x210),*(int *)(this + 0xb8),*(int *)(this + 0xbc),iVar2);
  }
  return (uint)(iVar1 == 1);
}

//===== 0x10020380 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: void __thiscall Wvfm::psd(double * *,int)const  */

void __thiscall Wvfm::psd(Wvfm *this,double **param_1,int param_2)

{
  int iVar1;
  int iVar2;
  double *pdVar3;
  double *pdVar4;
  double dVar5;
  int local_40;
  int local_3c;
  int local_38;
  int local_1c;
  int local_18;
  int local_14;
  int local_10;
  double local_c;
  
                    /* 0x20380  314  ?psd@Wvfm@@QBEXPAPANH@Z */
  iVar1 = param_2 / 2;
  local_c = 0.0;
  for (local_14 = 1; local_14 <= param_2; local_14 = local_14 + 1) {
    pdVar3 = param_1[4];
    *(undefined4 *)(pdVar3 + local_14) = 0;
    *(undefined4 *)((int)pdVar3 + local_14 * 8 + 4) = 0;
    pdVar3 = param_1[3];
    *(undefined4 *)(pdVar3 + local_14) = 0;
    *(undefined4 *)((int)pdVar3 + local_14 * 8 + 4) = 0;
    pdVar3 = param_1[2];
    *(undefined4 *)(pdVar3 + local_14) = 0;
    *(undefined4 *)((int)pdVar3 + local_14 * 8 + 4) = 0;
    pdVar3 = param_1[1];
    *(undefined4 *)(pdVar3 + local_14) = 0;
    *(undefined4 *)((int)pdVar3 + local_14 * 8 + 4) = 0;
  }
  iVar2 = (((*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1) - iVar1) / (param_2 / 2);
  local_10 = *(int *)(this + 0xb8);
  local_18 = local_10 + -1 + param_2;
  if (iVar2 != 0) {
    pdVar3 = dvector(1,param_2 << 1);
    pdVar4 = dvector(1,param_2);
    if ((pdVar3 == (double *)0x0) || (pdVar4 == (double *)0x0)) {
      if (pdVar3 != (double *)0x0) {
        free_dvector(pdVar3,1,param_2 << 1);
      }
      if (pdVar4 != (double *)0x0) {
        free_dvector(pdVar4,1,param_2);
      }
    }
    else {
      for (local_14 = 1; local_14 <= param_2; local_14 = local_14 + 1) {
        dVar5 = cos((_DAT_10038b78 * _DAT_10042250 * (double)local_14) / (double)(param_2 + 1));
        pdVar4[local_14] = (_DAT_10038b80 - dVar5) * _DAT_10038b88;
        local_c = pdVar4[local_14] * pdVar4[local_14] + local_c;
      }
      if (_DAT_10038b90 != (double)iVar2 * local_c) {
        for (local_1c = 1; local_1c <= iVar2; local_1c = local_1c + 1) {
          for (local_38 = 1; local_38 < 5; local_38 = local_38 + 1) {
            local_3c = 1;
            local_40 = 2;
            for (local_14 = local_10; local_14 <= local_18; local_14 = local_14 + 1) {
              dVar5 = sc_la(this,local_14,local_38);
              pdVar3[local_3c] = dVar5 * pdVar4[(local_14 - local_10) + 1];
              *(undefined4 *)(pdVar3 + local_40) = 0;
              *(undefined4 *)((int)pdVar3 + local_40 * 8 + 4) = 0;
              local_3c = local_3c + 2;
              local_40 = local_40 + 2;
            }
            dfour1(pdVar3,param_2,1);
            local_3c = 1;
            local_40 = 2;
            for (local_14 = 1; local_14 <= param_2; local_14 = local_14 + 1) {
              param_1[local_38][local_14] =
                   (pdVar3[local_40] * pdVar3[local_40] + pdVar3[local_3c] * pdVar3[local_3c]) /
                   ((double)iVar2 * local_c) + param_1[local_38][local_14];
              local_3c = local_3c + 2;
              local_40 = local_40 + 2;
            }
          }
          local_10 = local_10 + iVar1;
          local_18 = local_18 + iVar1;
        }
        for (local_38 = 1; local_38 < 5; local_38 = local_38 + 1) {
          for (local_14 = 1; local_14 <= param_2; local_14 = local_14 + 1) {
            dVar5 = log10((double)CONCAT44(*(undefined4 *)
                                            ((int)param_1[local_38] + local_14 * 8 + 4),
                                           *(undefined4 *)(param_1[local_38] + local_14)));
            param_1[local_38][local_14] = dVar5 * (double)_DAT_10038b98;
          }
        }
      }
      free_dvector(pdVar3,1,param_2 << 1);
      free_dvector(pdVar4,1,param_2);
    }
  }
  return;
}

//===== 0x10020781 =====

void FUN_10020781(void)

{
  FUN_1002078b();
  return;
}

//===== 0x1002078b =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1002078b(void)

{
  _DAT_10042250 = acos(-1.0);
  return;
}

//===== 0x100207b0 =====

/* public: int __thiscall Wvfm::rawRateCnvrt(struct TestOptions const &) */

int __thiscall Wvfm::rawRateCnvrt(Wvfm *this,TestOptions *param_1)

{
  float *pfVar1;
  int iVar2;
  int iVar3;
  float *pfVar4;
  int iVar5;
  float local_3c;
  int local_38;
  float *local_34;
  float *local_30;
  float *local_2c;
  double **local_28;
  int local_24;
  int local_20;
  float local_1c;
  int local_18;
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x207b0  329  ?rawRateCnvrt@Wvfm@@QAEHABUTestOptions@@@Z */
  fixCurrent(this);
  ObsInpSpec::laneOrder((ObsInpSpec *)(this + 0x210),(char *)(this + 0xdc));
  iVar2 = rows(this);
  iVar3 = rows(this);
  ObsInpSpec::boundaries((ObsInpSpec *)(this + 0x210),1,iVar3,iVar2);
  iVar2 = bgnEnd(this,param_1);
  if (iVar2 != 1) {
    return 1;
  }
  iVar2 = rows(this);
  ObsInpSpec::boundaries
            ((ObsInpSpec *)(this + 0x210),*(int *)(this + 0xb8),*(int *)(this + 0xbc),iVar2);
  local_8 = decimateP(this,1);
  if ((((*(int *)(this + 0xc0) != 5) && (local_8 == 0)) && (*(int *)(this + 0x1b0) < 8)) &&
     (*(int *)(this + 0x16c) != 2)) {
    iVar5 = 3 - (uint)(*(int *)(this + 0x16c) != 0);
    ObsInpSpec::rateChgAction((ObsInpSpec *)(this + 0x210),2,iVar5);
    iVar2 = rows(this);
    local_10 = (iVar2 + 1) / iVar5;
    iVar2 = local_10 * iVar5 * iVar5 + 1;
    iVar3 = cols(this);
    local_28 = dmatrix(1,iVar2,1,iVar3);
    if (local_28 == (double **)0x0) {
      *(undefined4 *)(this + 0x168) = 2;
      return 1;
    }
    local_30 = vector(1,4);
    local_34 = vector(1,4);
    pfVar4 = vector(1,4);
    if (((local_30 == (float *)0x0) || (local_34 == (float *)0x0)) || (pfVar4 == (float *)0x0)) {
      *(undefined4 *)(this + 0x168) = 2;
      return 1;
    }
    local_20 = 1;
    while (iVar3 = cols(this), local_20 <= iVar3) {
      iVar3 = bgni(this);
      local_14 = (iVar3 + -1) * iVar5 + 1;
      local_18 = bgni(this);
      while (iVar3 = endi(this), local_18 <= iVar3 + -3) {
        for (local_24 = 0; local_24 < 4; local_24 = local_24 + 1) {
          local_30[local_24 + 1] = (float)(local_18 + local_24);
          local_34[local_24 + 1] =
               (float)*(double *)
                       (*(int *)(*(int *)(this + 0xc4) + (local_18 + local_24) * 4) + local_20 * 8);
        }
        spline(local_30,local_34,4,local_34[2] - local_34[1],local_34[4] - local_34[3],pfVar4);
        for (local_24 = 0; local_24 < iVar5; local_24 = local_24 + 1) {
          for (local_38 = 0; local_38 < iVar5; local_38 = local_38 + 1) {
            local_1c = (float)local_38 / (float)iVar5 + (float)(local_18 + local_24);
            splint(local_30,local_34,pfVar4,4,local_1c,&local_3c);
            local_28[local_14][local_20] = (double)local_3c;
            local_14 = local_14 + 1;
          }
        }
        local_18 = local_18 + iVar5;
      }
      local_28[local_14][local_20] = (double)local_34[4];
      local_20 = local_20 + 1;
    }
    local_2c = vector(1,iVar2);
    if (local_2c == (float *)0x0) {
      *(undefined4 *)(this + 0x168) = 2;
      return 1;
    }
    iVar2 = bgni(this);
    local_14 = (iVar2 + -1) * iVar5 + 1;
    local_18 = bgni(this);
    while (iVar2 = endi(this), local_18 <= iVar2 + -3) {
      for (local_24 = 0; local_24 < 4; local_24 = local_24 + 1) {
        local_30[local_24 + 1] = (float)(local_18 + local_24);
        local_34[local_24 + 1] = *(float *)(*(int *)(this + 0x300) + (local_18 + local_24) * 4);
      }
      spline(local_30,local_34,4,local_34[2] - local_34[1],local_34[4] - local_34[3],pfVar4);
      for (local_24 = 0; local_24 < iVar5; local_24 = local_24 + 1) {
        for (local_38 = 0; local_38 < iVar5; local_38 = local_38 + 1) {
          local_1c = (float)local_38 / (float)iVar5 + (float)(local_18 + local_24);
          pfVar1 = local_2c + local_14;
          local_14 = local_14 + 1;
          splint(local_30,local_34,pfVar4,4,local_1c,pfVar1);
        }
      }
      local_18 = local_18 + iVar5;
    }
    local_2c[local_14] = local_34[4];
    free_vector(local_30,1,4);
    free_vector(local_34,1,4);
    free_vector(pfVar4,1,4);
    iVar2 = endi(this);
    iVar2 = (iVar2 * iVar5 - iVar5) + 1;
    iVar3 = bgni(this);
    pm(this,local_28,local_2c,local_14,(iVar3 * iVar5 - iVar5) + 1,iVar2);
    local_c = (*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1;
  }
  iVar2 = rows(this);
  ObsInpSpec::lmBoundaries
            ((ObsInpSpec *)(this + 0x210),*(int *)(this + 0xb8),*(int *)(this + 0xbc),iVar2);
  return 0;
}

//===== 0x10020d45 =====

void FUN_10020d45(void)

{
  FUN_10020d4f();
  return;
}

//===== 0x10020d4f =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10020d4f(void)

{
  _DAT_100422b8 = acos(-1.0);
  return;
}

//===== 0x10020d70 =====

/* public: __thiscall SSNODE::SSNODE(void) */

SSNODE * __thiscall SSNODE::SSNODE(SSNODE *this)

{
                    /* 0x20d70  19  ??0SSNODE@@QAE@XZ */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  return this;
}

//===== 0x10020daf =====

/* public: void __thiscall SSNODE::debug(void)const  */

void __thiscall SSNODE::debug(SSNODE *this)

{
  float fVar1;
  
                    /* 0x20daf  130  ?debug@SSNODE@@QBEXXZ */
  printf(s_SSNODE____p_100405fc);
  Wvfm::annotate((Wvfm *)this);
  printf(s_fltwid____4d_1004060c);
  SWold(this);
  printf(s_SWold____4d_10040620);
  Annotate::getNumCurrFix((Annotate *)this);
  printf(s_start____4d_10040634);
  SW::alignedLength((SW *)this);
  printf(s_finish____4d_10040648);
  rdlen(this);
  printf(s_rdlen____4d_1004065c);
  fVar1 = thresh(this);
  printf(s_thresh____4_2f_10040670,(double)fVar1);
  return;
}

//===== 0x10020e5b =====

/* public: __thiscall QualCtrl::QualCtrl(void) */

QualCtrl * __thiscall QualCtrl::QualCtrl(QualCtrl *this)

{
  int local_8;
  
                    /* 0x20e5b  16  ??0QualCtrl@@QAE@XZ */
  FUN_100241b0(this,8,0xc,ShftVect::ShftVect);
  *(undefined4 *)(this + 0xc0) = 0;
  *(undefined4 *)(this + 0xc4) = 0;
  *(undefined4 *)(this + 200) = 0;
  SSNODE::SSNODE((SSNODE *)(this + 0xcc));
  *(undefined4 *)(this + 0xe0) = 0;
  for (local_8 = 0; local_8 < 0xc; local_8 = local_8 + 1) {
    *(undefined4 *)(this + local_8 * 4 + 0x60) = 0;
    *(undefined4 *)(this + local_8 * 4 + 0x90) = 0;
  }
  return this;
}

//===== 0x10020ef8 =====

/* public: char const * __thiscall QualCtrl::shft(int,char *,int)const  */

char * __thiscall QualCtrl::shft(QualCtrl *this,int param_1,char *param_2,int param_3)

{
  short sVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  ShftVect local_c [8];
  
                    /* 0x20ef8  396  ?shft@QualCtrl@@QBEPBDHPADH@Z */
  if ((0xe < param_3) && (iVar2 = nseg(this), param_1 < iVar2)) {
    shft(this,(int)local_c);
    sVar1 = ShftVect::s(local_c,4);
    iVar4 = (int)sVar1;
    sVar1 = ShftVect::s(local_c,3);
    iVar2 = (int)sVar1;
    sVar1 = ShftVect::s(local_c,2);
    iVar3 = (int)sVar1;
    sVar1 = ShftVect::s(local_c,1);
    sprintf(param_2,s___2hd__2hd__2hd__2hd__10040684,(int)sVar1,iVar3,iVar2,iVar4);
    return param_2;
  }
  strcpy(param_2,&DAT_1004069c);
  return param_2;
}

//===== 0x10020f8a =====

/* public: __thiscall QualCtrl::QualCtrl(class QualCtrl const &) */

QualCtrl * __thiscall QualCtrl::QualCtrl(QualCtrl *this,QualCtrl *param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x20f8a  15  ??0QualCtrl@@QAE@ABV0@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003712f;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  FUN_100241b0(this,8,0xc,ShftVect::ShftVect);
  *(undefined4 *)(this + 0xc0) = 0;
  *(undefined4 *)(this + 0xc4) = 0;
  *(undefined4 *)(this + 200) = 0;
  SSNODE::SSNODE((SSNODE *)(this + 0xcc));
  local_8 = 0;
  *(undefined4 *)(this + 0xe0) = 0;
  operator=(this,param_1);
  ExceptionList = local_10;
  return this;
}

//===== 0x10021027 =====

/* public: class QualCtrl const & __thiscall QualCtrl::operator=(class QualCtrl const &) */

QualCtrl * __thiscall QualCtrl::operator=(QualCtrl *this,QualCtrl *param_1)

{
  undefined4 uVar1;
  size_t sVar2;
  void *pvVar3;
  int iVar4;
  QualCtrl *pQVar5;
  QualCtrl *pQVar6;
  int local_8;
  
                    /* 0x21027  50  ??4QualCtrl@@QAEABV0@ABV0@@Z */
  if (this != param_1) {
    for (local_8 = 0; local_8 < 0xc; local_8 = local_8 + 1) {
      uVar1 = *(undefined4 *)(param_1 + local_8 * 8 + 4);
      *(undefined4 *)(this + local_8 * 8) = *(undefined4 *)(param_1 + local_8 * 8);
      *(undefined4 *)(this + local_8 * 8 + 4) = uVar1;
      *(undefined4 *)(this + local_8 * 4 + 0x60) = *(undefined4 *)(param_1 + local_8 * 4 + 0x60);
      *(undefined4 *)(this + local_8 * 4 + 0x90) = *(undefined4 *)(param_1 + local_8 * 4 + 0x90);
    }
    *(undefined4 *)(this + 0xc0) = *(undefined4 *)(param_1 + 0xc0);
    *(undefined4 *)(this + 0xc4) = *(undefined4 *)(param_1 + 0xc4);
    *(undefined4 *)(this + 200) = *(undefined4 *)(param_1 + 200);
    pQVar5 = param_1 + 0xcc;
    pQVar6 = this + 0xcc;
    for (iVar4 = 5; iVar4 != 0; iVar4 = iVar4 + -1) {
      *(undefined4 *)pQVar6 = *(undefined4 *)pQVar5;
      pQVar5 = pQVar5 + 4;
      pQVar6 = pQVar6 + 4;
    }
    if (*(int *)(this + 0xe0) != 0) {
      operator_delete(*(void **)(this + 0xe0));
      *(undefined4 *)(this + 0xe0) = 0;
    }
    if (*(int *)(param_1 + 0xe0) != 0) {
      sVar2 = strlen(*(char **)(param_1 + 0xe0));
      pvVar3 = operator_new(sVar2 + 1);
      *(void **)(this + 0xe0) = pvVar3;
      if (*(int *)(this + 0xe0) != 0) {
        strcpy(*(char **)(this + 0xe0),*(char **)(param_1 + 0xe0));
      }
    }
  }
  return this;
}

//===== 0x10021186 =====

/* public: __thiscall QualCtrl::~QualCtrl(void) */

void __thiscall QualCtrl::~QualCtrl(QualCtrl *this)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x21186  37  ??1QualCtrl@@QAE@XZ */
  puStack_c = &LAB_10037148;
  local_10 = ExceptionList;
  local_8 = 0;
  ExceptionList = &local_10;
  if (*(int *)(this + 0xe0) != 0) {
    ExceptionList = &local_10;
    operator_delete(*(void **)(this + 0xe0));
    *(undefined4 *)(this + 0xe0) = 0;
  }
  local_8 = 0xffffffff;
  BandStat::~BandStat((BandStat *)(this + 0xcc));
  ExceptionList = local_10;
  return;
}

//===== 0x100211ff =====

/* public: void __thiscall QualCtrl::debug(void)const  */

void __thiscall QualCtrl::debug(QualCtrl *this)

{
  int local_8;
  
                    /* 0x211ff  128  ?debug@QualCtrl@@QBEXXZ */
  printf(s_QualCtrl____p_100406a0,this);
  printf(s_elapsed__d_Sec__100406b0,*(int *)(this + 0xc4) - *(int *)(this + 0xc0));
  SSNODE::debug((SSNODE *)(this + 0xcc));
  for (local_8 = 0; local_8 < *(int *)(this + 200); local_8 = local_8 + 1) {
    printf(s_idx__d__fbw__2d__bspac__2d_100406c4,local_8,*(undefined4 *)(this + local_8 * 4 + 0x60),
           *(undefined4 *)(this + local_8 * 4 + 0x90));
    ShftVect::debug((ShftVect *)(this + local_8 * 8),0);
  }
  return;
}

//===== 0x100212aa =====

/* public: __thiscall RdrOut::RdrOut(void) */

RdrOut * __thiscall RdrOut::RdrOut(RdrOut *this)

{
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x212aa  18  ??0RdrOut@@QAE@XZ */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003716a;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  BandStatArray::BandStatArray((BandStatArray *)(this + 0x1c));
  local_8 = 0;
  Wvfm::Wvfm((Wvfm *)(this + 0x28));
  local_8 = CONCAT31(local_8._1_3_,1);
  QualCtrl::QualCtrl((QualCtrl *)(this + 0x330));
  *(undefined4 *)(this + 0x4c0) = 0;
  *(undefined4 *)(this + 0x4c4) = 0;
  *(undefined4 *)(this + 0x4c8) = 0;
  *(undefined4 *)(this + 0x4cc) = 0;
  *(undefined4 *)(this + 0x4d0) = 0;
  *(undefined4 *)(this + 0x4d4) = 0;
  *(undefined4 *)(this + 0x4d8) = 0;
  *(undefined4 *)(this + 0x4dc) = 0;
  *(undefined4 *)(this + 0x4e0) = 0;
  *(undefined4 *)(this + 0x4e4) = 0;
  memset(this + 0x14,0,6);
  for (local_14 = 0; local_14 < 0x15; local_14 = local_14 + 1) {
    *(undefined4 *)(this + local_14 * 8 + 0x418) = 0;
    *(undefined4 *)(this + local_14 * 8 + 0x41c) = 0;
  }
  ExceptionList = local_10;
  return this;
}

//===== 0x1002140b =====

/* public: class RdrOut const & __thiscall RdrOut::operator=(class RdrOut const &) */

RdrOut * __thiscall RdrOut::operator=(RdrOut *this,RdrOut *param_1)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  double *pdVar4;
  int local_8;
  
                    /* 0x2140b  51  ??4RdrOut@@QAEABV0@ABV0@@Z */
  if (param_1 != this) {
    release(this);
    *(undefined4 *)this = *(undefined4 *)param_1;
    *(undefined4 *)(this + 4) = *(undefined4 *)(param_1 + 4);
    *(undefined4 *)(this + 8) = *(undefined4 *)(param_1 + 8);
    if (*(int *)(this + 8) != 0) {
      piVar3 = ivector(1,*(long *)(this + 8));
      *(int **)(this + 0xc) = piVar3;
      for (local_8 = 1; local_8 <= *(int *)(this + 8); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)(this + 0xc) + local_8 * 4) =
             *(undefined4 *)(*(int *)(param_1 + 0xc) + local_8 * 4);
      }
    }
    memcpy(this + 0x14,param_1 + 0x14,6);
    BandStatArray::operator=((BandStatArray *)(this + 0x1c),(BandStatArray *)(param_1 + 0x1c));
    Wvfm::operator=((Wvfm *)(this + 0x28),(Wvfm *)(param_1 + 0x28));
    QualCtrl::operator=((QualCtrl *)(this + 0x330),(QualCtrl *)(param_1 + 0x330));
    *(undefined4 *)(this + 0x4e4) = *(undefined4 *)(param_1 + 0x4e4);
    for (local_8 = 0; local_8 < 0x15; local_8 = local_8 + 1) {
      *(undefined4 *)(this + local_8 * 8 + 0x418) = *(undefined4 *)(param_1 + local_8 * 8 + 0x418);
      *(undefined4 *)(this + local_8 * 8 + 0x41c) = *(undefined4 *)(param_1 + local_8 * 8 + 0x41c);
    }
    if (*(int *)(param_1 + 0x4c0) != 0) {
      pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
      *(double **)(this + 0x4c0) = pdVar4;
      for (local_8 = 1; local_8 <= *(int *)(this + 0x4dc) * 2; local_8 = local_8 + 1) {
        iVar1 = *(int *)(param_1 + 0x4c0);
        iVar2 = *(int *)(this + 0x4c0);
        *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
        *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
      }
    }
    if (*(int *)(param_1 + 0x4c4) != 0) {
      pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
      *(double **)(this + 0x4c4) = pdVar4;
      for (local_8 = 1; local_8 <= *(int *)(this + 0x4dc) * 2; local_8 = local_8 + 1) {
        iVar1 = *(int *)(param_1 + 0x4c4);
        iVar2 = *(int *)(this + 0x4c4);
        *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
        *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
      }
    }
    if (*(int *)(param_1 + 0x4c8) != 0) {
      pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
      *(double **)(this + 0x4c8) = pdVar4;
      for (local_8 = 1; local_8 <= *(int *)(this + 0x4dc) * 2; local_8 = local_8 + 1) {
        iVar1 = *(int *)(param_1 + 0x4c8);
        iVar2 = *(int *)(this + 0x4c8);
        *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
        *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
      }
    }
    if (*(int *)(param_1 + 0x4cc) != 0) {
      pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
      *(double **)(this + 0x4cc) = pdVar4;
      for (local_8 = 1; local_8 <= *(int *)(this + 0x4dc) * 2; local_8 = local_8 + 1) {
        iVar1 = *(int *)(param_1 + 0x4cc);
        iVar2 = *(int *)(this + 0x4cc);
        *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
        *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
      }
    }
    if (*(int *)(param_1 + 0x4d0) != 0) {
      pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
      *(double **)(this + 0x4d0) = pdVar4;
      for (local_8 = 1; local_8 <= *(int *)(this + 0x4dc) * 2; local_8 = local_8 + 1) {
        iVar1 = *(int *)(param_1 + 0x4d0);
        iVar2 = *(int *)(this + 0x4d0);
        *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
        *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
      }
    }
    if (*(int *)(param_1 + 0x4d4) != 0) {
      piVar3 = ivector(1,*(long *)(this + 0x4e0));
      *(int **)(this + 0x4d4) = piVar3;
      for (local_8 = 1; local_8 <= *(int *)(this + 0x4e0); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)(this + 0x4d4) + local_8 * 4) =
             *(undefined4 *)(*(int *)(param_1 + 0x4d4) + local_8 * 4);
      }
    }
    if (*(int *)(param_1 + 0x4d8) != 0) {
      piVar3 = ivector(1,*(long *)(this + 0x4e0));
      *(int **)(this + 0x4d8) = piVar3;
      for (local_8 = 1; local_8 <= *(int *)(this + 0x4e0); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)(this + 0x4d8) + local_8 * 4) =
             *(undefined4 *)(*(int *)(param_1 + 0x4d8) + local_8 * 4);
      }
    }
  }
  return this;
}

//===== 0x10021871 =====

/* private: void __thiscall RdrOut::release(void) */

void __thiscall RdrOut::release(RdrOut *this)

{
                    /* 0x21871  335  ?release@RdrOut@@AAEXXZ */
  if (*(int *)(this + 0xc) != 0) {
    free_ivector(*(int **)(this + 0xc),1,*(long *)(this + 8));
    *(undefined4 *)(this + 0xc) = 0;
  }
  if (*(int *)(this + 0x4c0) != 0) {
    free_dvector(*(double **)(this + 0x4c0),1,*(int *)(this + 0x4dc) << 1);
    *(undefined4 *)(this + 0x4c0) = 0;
  }
  if (*(int *)(this + 0x4c8) != 0) {
    free_dvector(*(double **)(this + 0x4c8),1,*(int *)(this + 0x4dc) << 1);
    *(undefined4 *)(this + 0x4c8) = 0;
  }
  if (*(int *)(this + 0x4c4) != 0) {
    free_dvector(*(double **)(this + 0x4c4),1,*(int *)(this + 0x4dc) << 1);
    *(undefined4 *)(this + 0x4c4) = 0;
  }
  if (*(int *)(this + 0x4cc) != 0) {
    free_dvector(*(double **)(this + 0x4cc),1,*(int *)(this + 0x4dc) << 1);
    *(undefined4 *)(this + 0x4cc) = 0;
  }
  if (*(int *)(this + 0x4d0) != 0) {
    free_dvector(*(double **)(this + 0x4d0),1,*(int *)(this + 0x4dc) << 1);
    *(undefined4 *)(this + 0x4d0) = 0;
  }
  if (*(int *)(this + 0x4d4) != 0) {
    free_ivector(*(int **)(this + 0x4d4),1,*(long *)(this + 0x4e0));
    *(undefined4 *)(this + 0x4d4) = 0;
  }
  if (*(int *)(this + 0x4d8) != 0) {
    free_ivector(*(int **)(this + 0x4d8),1,*(long *)(this + 0x4e0));
    *(undefined4 *)(this + 0x4d8) = 0;
  }
  return;
}

//===== 0x10021a32 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: __thiscall RdrOut::RdrOut(class Wvfm const &) */

RdrOut * __thiscall RdrOut::RdrOut(RdrOut *this,Wvfm *param_1)

{
  int iVar1;
  char *_Source;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x21a32  17  ??0RdrOut@@QAE@ABVWvfm@@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003719b;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 1;
  iVar1 = Wvfm::bgni(param_1);
  *(int *)(this + 4) = iVar1 + 1;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 1;
  BandStatArray::BandStatArray((BandStatArray *)(this + 0x1c));
  local_8 = 0;
  Wvfm::Wvfm((Wvfm *)(this + 0x28));
  local_8._0_1_ = 1;
  QualCtrl::QualCtrl((QualCtrl *)(this + 0x330));
  local_8 = CONCAT31(local_8._1_3_,2);
  *(undefined4 *)(this + 0x4c0) = 0;
  *(undefined4 *)(this + 0x4c4) = 0;
  *(undefined4 *)(this + 0x4c8) = 0;
  *(undefined4 *)(this + 0x4cc) = 0;
  *(undefined4 *)(this + 0x4d0) = 0;
  *(undefined4 *)(this + 0x4d4) = 0;
  *(undefined4 *)(this + 0x4d8) = 0;
  *(undefined4 *)(this + 0x4dc) = 0;
  *(undefined4 *)(this + 0x4e0) = 0;
  *(undefined4 *)(this + 0x4e4) = 0;
  _Source = Wvfm::lnordr(param_1);
  strcpy((char *)(this + 0x14),_Source);
  for (local_14 = 1; local_14 < 0x15; local_14 = local_14 + 1) {
    *(double *)(this + local_14 * 8 + 0x418) =
         _DAT_10038cf8 / _DAT_10038d00 + (double)local_14 * _DAT_10038cf0;
  }
  ExceptionList = local_10;
  return this;
}

//===== 0x10021bad =====

void FUN_10021bad(void)

{
  FUN_10021bb7();
  return;
}

//===== 0x10021bb7 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10021bb7(void)

{
  _DAT_10042320 = acos(-1.0);
  return;
}

//===== 0x10021bd1 =====

/* public: __thiscall RdrOut::~RdrOut(void) */

void __thiscall RdrOut::~RdrOut(RdrOut *this)

{
  void *local_10;
  undefined1 *puStack_c;
  int local_8;
  
                    /* 0x21bd1  38  ??1RdrOut@@QAE@XZ */
  puStack_c = &LAB_100371cc;
  local_10 = ExceptionList;
  local_8 = 2;
  ExceptionList = &local_10;
  release(this);
  local_8._0_1_ = 1;
  QualCtrl::~QualCtrl((QualCtrl *)(this + 0x330));
  local_8 = (uint)local_8._1_3_ << 8;
  Wvfm::~Wvfm((Wvfm *)(this + 0x28));
  local_8 = 0xffffffff;
  BandStatArray::~BandStatArray((BandStatArray *)(this + 0x1c));
  ExceptionList = local_10;
  return;
}

//===== 0x10021c3d =====

/* public: int __thiscall RdrOut::add(int,int,int,class SegRead const &) */

int __thiscall RdrOut::add(RdrOut *this,int param_1,int param_2,int param_3,SegRead *param_4)

{
  ShftVect *pSVar1;
  BandStatArray *pBVar2;
  Wvfm *pWVar3;
  int iVar4;
  int *piVar5;
  int local_c;
  int local_8;
  
                    /* 0x21c3d  65  ?add@RdrOut@@QAEHHHHABVSegRead@@@Z */
  pSVar1 = (ShftVect *)FUN_100241e0((int)param_4);
  QualCtrl::shft((QualCtrl *)(this + 0x330),param_1 + -1,pSVar1);
  QualCtrl::fbw((QualCtrl *)(this + 0x330),param_1 + -1,param_2);
  QualCtrl::bspac((QualCtrl *)(this + 0x330),param_1 + -1,param_3);
  QualCtrl::nseg((QualCtrl *)(this + 0x330),param_1);
  if (param_1 == 1) {
    pBVar2 = (BandStatArray *)FUN_10026690((int)param_4);
    BandStatArray::operator=((BandStatArray *)(this + 0x1c),pBVar2);
    pWVar3 = (Wvfm *)SW::alignedLength((SW *)param_4);
    Wvfm::operator=((Wvfm *)(this + 0x28),pWVar3);
    local_8 = 1;
  }
  else {
    local_8 = was_at(this,param_4,param_1);
    if (local_8 == 1) {
      join(this,param_4);
    }
  }
  if (local_8 != 0) {
    if (*(int *)(this + 0xc) != 0) {
      free_ivector(*(int **)(this + 0xc),1,*(long *)(this + 8));
      *(undefined4 *)(this + 0xc) = 0;
    }
    pWVar3 = (Wvfm *)FUN_10026690((int)param_4);
    iVar4 = Wvfm::annotate(pWVar3);
    *(int *)(this + 8) = iVar4;
    if (*(int *)(this + 8) != 0) {
      piVar5 = ivector(1,*(long *)(this + 8));
      *(int **)(this + 0xc) = piVar5;
      if (*(int *)(this + 0xc) != 0) {
        for (local_c = 1; local_c <= *(int *)(this + 8); local_c = local_c + 1) {
          iVar4 = local_c + -1;
          pBVar2 = (BandStatArray *)FUN_10026690((int)param_4);
          iVar4 = BandStatArray::posn(pBVar2,iVar4);
          *(int *)(*(int *)(this + 0xc) + local_c * 4) = iVar4;
        }
        return local_8;
      }
    }
    local_8 = 0;
  }
  return local_8;
}

//===== 0x10021dca =====

/* private: void __thiscall RdrOut::join(class SegRead const &) */

void __thiscall RdrOut::join(RdrOut *this,SegRead *param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  int iVar5;
  BandStatArray *pBVar6;
  Wvfm *pWVar7;
  Wvfm *this_00;
  BandStatArray *this_01;
  int iVar8;
  float fVar9;
  float fVar10;
  double dVar11;
  double dVar12;
  int local_34;
  int local_20;
  int local_1c;
  int local_18;
  int local_10;
  int local_8;
  
                    /* 0x21dca  253  ?join@RdrOut@@AAEXABVSegRead@@@Z */
  local_18 = BandStatArray::posn((BandStatArray *)(this + 0x1c),*(int *)this + -1);
  local_18 = local_18 + -9;
  iVar5 = *(int *)(this + 0x10) + -1;
  pBVar6 = (BandStatArray *)FUN_10026690((int)param_1);
  local_20 = BandStatArray::posn(pBVar6,iVar5);
  local_20 = local_20 + -9;
  pWVar7 = wvfm(this);
  iVar5 = Wvfm::rows(pWVar7);
  iVar5 = 0x14 - ((iVar5 - local_18) + 1);
  iVar8 = 1 - local_20;
  if (iVar5 < 1) {
    if (0 < iVar8) {
      local_18 = local_18 + iVar8;
      local_20 = local_20 + iVar8;
    }
  }
  else {
    local_18 = local_18 - iVar5;
    local_20 = local_20 - iVar5;
  }
  for (local_8 = 1; local_8 < 0x15; local_8 = local_8 + 1) {
    uVar1 = *(undefined4 *)(this + local_8 * 8 + 0x418);
    uVar2 = *(undefined4 *)(this + local_8 * 8 + 0x41c);
    uVar3 = *(undefined4 *)(this + (0x14 - local_8) * 8 + 0x420);
    uVar4 = *(undefined4 *)(this + (0x14 - local_8) * 8 + 0x424);
    local_1c = local_18 + -1 + local_8;
    local_10 = local_20 + -1 + local_8;
    for (local_34 = 1; local_34 < 5; local_34 = local_34 + 1) {
      iVar5 = local_1c;
      iVar8 = local_34;
      pWVar7 = wvfm(this);
      dVar11 = Wvfm::sc_la(pWVar7,iVar5,iVar8);
      iVar5 = local_10;
      iVar8 = local_34;
      pWVar7 = (Wvfm *)SW::alignedLength((SW *)param_1);
      dVar12 = Wvfm::sc_la(pWVar7,iVar5,iVar8);
      dVar11 = (double)CONCAT44(uVar4,uVar3) * dVar12 + (double)CONCAT44(uVar2,uVar1) * dVar11;
      iVar5 = local_1c;
      iVar8 = local_34;
      pWVar7 = wvfm(this);
      Wvfm::sc_la_set(pWVar7,iVar5,iVar8,dVar11);
      if (local_34 == 1) {
        iVar5 = local_1c;
        pWVar7 = wvfm(this);
        fVar9 = Wvfm::getCurr(pWVar7,iVar5);
        iVar5 = local_10;
        pWVar7 = (Wvfm *)SW::alignedLength((SW *)param_1);
        fVar10 = Wvfm::getCurr(pWVar7,iVar5);
        fVar9 = (float)(double)CONCAT44(uVar4,uVar3) * fVar10 +
                (float)(double)CONCAT44(uVar2,uVar1) * fVar9;
        iVar5 = local_1c;
        pWVar7 = wvfm(this);
        Wvfm::setCurr(pWVar7,iVar5,fVar9);
      }
    }
  }
  iVar5 = local_10 + 1;
  pWVar7 = (Wvfm *)SW::alignedLength((SW *)param_1);
  this_00 = wvfm(this);
  Wvfm::append(this_00,pWVar7,local_1c,iVar5);
  iVar5 = *(int *)(this + 0x10);
  iVar8 = *(int *)this + -1;
  pBVar6 = (BandStatArray *)FUN_10026690((int)param_1);
  this_01 = bandstat(this);
  BandStatArray::append(this_01,pBVar6,iVar8,iVar5);
  return;
}

//===== 0x10022007 =====

/* private: void __thiscall RdrOut::closesTo(int,int &,int &)const  */

void __thiscall RdrOut::closesTo(RdrOut *this,int param_1,int *param_2,int *param_3)

{
  int iVar1;
  int iVar2;
  int local_18;
  int local_14;
  int local_10;
  int local_c;
  
                    /* 0x22007  112  ?closesTo@RdrOut@@ABEXHAAH0@Z */
  local_c = 1;
  local_18 = *(int *)(this + 8);
  local_10 = 1;
  local_14 = local_18;
  while( true ) {
    if (local_18 < local_c) {
      iVar2 = abs(param_1 - *(int *)(*(int *)(this + 0xc) + local_10 * 4));
      iVar1 = abs(*(int *)(*(int *)(this + 0xc) + local_14 * 4) - param_1);
      if (iVar2 < iVar1) {
        *param_2 = iVar2;
        *param_3 = local_10;
      }
      else {
        *param_2 = iVar1;
        *param_3 = local_14;
      }
      return;
    }
    iVar1 = (local_18 + local_c) / 2;
    iVar2 = *(int *)(*(int *)(this + 0xc) + iVar1 * 4);
    if (param_1 == iVar2) break;
    if (param_1 < iVar2) {
      local_18 = iVar1 + -1;
      local_14 = iVar1;
    }
    else {
      local_c = iVar1 + 1;
      local_10 = iVar1;
    }
  }
  *param_2 = 0;
  *param_3 = iVar1;
  return;
}

//===== 0x1002210b =====

/* private: int __thiscall RdrOut::was_at(class SegRead const &,int) */

int __thiscall RdrOut::was_at(RdrOut *this,SegRead *param_1,int param_2)

{
  RdrOut RVar1;
  RdrOut RVar2;
  short sVar3;
  short sVar4;
  Wvfm *this_00;
  int iVar5;
  BandStatArray *pBVar6;
  int iVar7;
  QualCtrl *pQVar8;
  ShftVect *pSVar9;
  undefined1 *puVar10;
  undefined1 local_48 [8];
  undefined1 local_40 [8];
  int local_38;
  int local_34;
  int local_30;
  int local_2c;
  int local_28;
  uint local_24;
  int local_20;
  int local_18;
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x2210b  435  ?was_at@RdrOut@@AAEHABVSegRead@@H@Z */
  local_8 = 4;
  this_00 = (Wvfm *)FUN_10026690((int)param_1);
  local_c = Wvfm::annotate(this_00);
  local_10 = 0;
  local_20 = Annotate::getNumCurrFix((Annotate *)param_1);
  local_20 = local_20 - (*(int *)(this + 4) + (param_2 + -2) * 0x76c);
  for (local_24 = 1; local_24 < 0xb; local_24 = local_24 + 1) {
    local_2c = *(int *)(&UNK_10038ba8 + local_24 * 4);
    for (local_28 = 0; local_28 < 4; local_28 = local_28 + 1) {
      if (local_2c <= local_c) {
        RVar1 = this[local_28 + 0x14];
        iVar5 = local_2c + -1;
        pBVar6 = (BandStatArray *)FUN_10026690((int)param_1);
        RVar2 = (RdrOut)BandStatArray::call(pBVar6,iVar5);
        if (RVar1 == RVar2) break;
      }
    }
    local_28 = local_28 + 1;
    if (local_28 != 5) {
      iVar5 = local_2c + -1;
      pBVar6 = (BandStatArray *)FUN_10026690((int)param_1);
      iVar7 = BandStatArray::posn(pBVar6,iVar5);
      puVar10 = local_40;
      iVar5 = local_28;
      pQVar8 = qualctrl(this);
      pSVar9 = (ShftVect *)QualCtrl::shft(pQVar8,(int)puVar10);
      sVar3 = ShftVect::s(pSVar9,iVar5);
      puVar10 = local_48;
      iVar5 = local_28;
      pQVar8 = qualctrl(this);
      pSVar9 = (ShftVect *)QualCtrl::shft(pQVar8,(int)puVar10);
      sVar4 = ShftVect::s(pSVar9,iVar5);
      local_34 = (int)sVar4 + local_20 + (iVar7 - sVar3);
      closesTo(this,local_34,&local_30,&local_38);
      if (local_30 < local_8) {
        local_10 = 1;
        local_18 = local_2c;
        local_14 = local_38;
        local_8 = local_30;
        if (local_30 == 0) break;
      }
    }
  }
  if (local_10 == 1) {
    *(int *)this = *(int *)this + (local_14 - *(int *)(this + 0x10));
    *(int *)(this + 0x10) = local_18;
  }
  return local_10;
}

//===== 0x100222c1 =====

/* public: void __thiscall RdrOut::Edit(char const *) */

void __thiscall RdrOut::Edit(RdrOut *this,char *param_1)

{
  int iVar1;
  
                    /* 0x222c1  59  ?Edit@RdrOut@@QAEXPBD@Z */
  iVar1 = Wvfm::annotate((Wvfm *)(this + 0x1c));
  BandStatArray::posn((BandStatArray *)(this + 0x1c),0);
  BandStatArray::posn((BandStatArray *)(this + 0x1c),iVar1 + -1);
  bandqual(this);
  pickcuts(this,param_1);
  QualCtrl::stopTimer((QualCtrl *)(this + 0x330));
  return;
}

//===== 0x10022325 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall RdrOut::cutoff(int,class SSNODE &)const  */

void __thiscall RdrOut::cutoff(RdrOut *this,int param_1,SSNODE *param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  int *piVar5;
  uint local_5c;
  int local_44;
  int local_40;
  int local_30;
  int local_2c;
  uint local_28;
  int local_20;
  int local_1c;
  int local_10;
  int local_c;
  
                    /* 0x22325  122  ?cutoff@RdrOut@@ABEXHAAVSSNODE@@@Z */
  local_c = 0;
  Wvfm::annotate((Wvfm *)param_2,*(int *)(&DAT_10038bd8 + param_1 * 4));
  iVar1 = Wvfm::annotate((Wvfm *)param_2);
  if (iVar1 <= *(int *)(this + 0x4dc)) {
    iVar2 = (*(int *)(&DAT_10038bd8 + param_1 * 4) + 1) / 2;
    iVar1 = *(int *)(&DAT_10038bd8 + param_1 * 4);
    local_20 = 0;
    local_2c = 0;
    local_30 = 0;
    local_28 = 0;
    for (local_10 = 1; local_10 <= iVar2 * 2; local_10 = local_10 + 2) {
      iVar3 = Wvfm::annotate((Wvfm *)param_2);
      *(double *)(*(int *)(this + 0x4c8) + local_10 * 8) = _DAT_10038d08 / (double)iVar3;
      iVar3 = *(int *)(this + 0x4c8);
      *(undefined4 *)(iVar3 + 8 + local_10 * 8) = 0;
      *(undefined4 *)(iVar3 + 0xc + local_10 * 8) = 0;
    }
    for (; local_10 <= (*(int *)(this + 0x4dc) - (iVar1 - iVar2)) * 2; local_10 = local_10 + 1) {
      iVar3 = *(int *)(this + 0x4c8);
      *(undefined4 *)(iVar3 + local_10 * 8) = 0;
      *(undefined4 *)(iVar3 + 4 + local_10 * 8) = 0;
    }
    for (; local_10 <= *(int *)(this + 0x4dc) * 2; local_10 = local_10 + 2) {
      iVar1 = Wvfm::annotate((Wvfm *)param_2);
      *(double *)(*(int *)(this + 0x4c8) + local_10 * 8) = _DAT_10038d08 / (double)iVar1;
      iVar1 = *(int *)(this + 0x4c8);
      *(undefined4 *)(iVar1 + 8 + local_10 * 8) = 0;
      *(undefined4 *)(iVar1 + 0xc + local_10 * 8) = 0;
    }
    dfour1(*(double **)(this + 0x4c8),*(ulong *)(this + 0x4dc),1);
    FUN_10034b00(*(int *)(this + 0x4c0),*(int *)(this + 0x4c8),*(int *)(this + 0x4cc),
                 *(int *)(this + 0x4dc));
    FUN_10034b00(*(int *)(this + 0x4c4),*(int *)(this + 0x4c8),*(int *)(this + 0x4d0),
                 *(int *)(this + 0x4dc));
    dfour1(*(double **)(this + 0x4cc),*(ulong *)(this + 0x4dc),-1);
    dfour1(*(double **)(this + 0x4d0),*(ulong *)(this + 0x4dc),-1);
    local_10 = 1;
    for (local_1c = 1; local_1c <= *(int *)(this + 0x4e0) * 2; local_1c = local_1c + 2) {
      local_5c = (uint)(*(double *)(*(int *)(this + 0x4d0) + local_1c * 8) <=
                       *(double *)(*(int *)(this + 0x4cc) + local_1c * 8));
      if (local_5c != 0) {
        local_20 = local_20 + 1;
      }
      if (local_10 != 1) {
        if ((int)(local_5c - local_28) < 1) {
          if ((int)(local_5c - local_28) < 0) {
            local_30 = local_30 + 1;
            *(int *)(*(int *)(this + 0x4d4) + local_30 * 4) = local_10 + -1;
          }
        }
        else {
          local_2c = local_2c + 1;
          *(int *)(*(int *)(this + 0x4d8) + local_2c * 4) = local_10 + -1;
        }
      }
      local_28 = local_5c;
      local_10 = local_10 + 1;
    }
    if (local_20 != 0) {
      if (local_20 == *(int *)(this + 0x4e0)) {
        iS1((RdrOut *)param_2,1);
        BandStat::bbgn((BandStat *)param_2,*(int *)(this + 0x4e0));
      }
      else if (local_2c == 0) {
        iS1((RdrOut *)param_2,1);
        BandStat::bbgn((BandStat *)param_2,*(int *)(*(int *)(this + 0x4d4) + 4));
      }
      else if (local_30 == 0) {
        iS1((RdrOut *)param_2,*(int *)(*(int *)(this + 0x4d8) + 4) + 1);
        BandStat::bbgn((BandStat *)param_2,*(int *)(this + 0x4e0));
      }
      else {
        local_44 = local_2c;
        local_40 = local_30;
        piVar4 = ivector(1,local_2c + 1);
        piVar5 = ivector(1,local_30 + 1);
        iVar1 = *(int *)(*(int *)(this + 0x4d4) + local_30 * 4);
        iVar2 = *(int *)(*(int *)(this + 0x4d8) + local_2c * 4);
        if (*(int *)(*(int *)(this + 0x4d4) + 4) < *(int *)(*(int *)(this + 0x4d8) + 4)) {
          piVar4[1] = 1;
          for (local_10 = 1; local_10 <= local_2c; local_10 = local_10 + 1) {
            piVar4[local_10 + 1] = *(int *)(*(int *)(this + 0x4d8) + local_10 * 4);
          }
          local_44 = local_2c + 1;
        }
        else {
          for (local_10 = 1; local_10 <= local_2c; local_10 = local_10 + 1) {
            piVar4[local_10] = *(int *)(*(int *)(this + 0x4d8) + local_10 * 4);
          }
        }
        for (local_10 = 1; local_10 <= local_30; local_10 = local_10 + 1) {
          piVar5[local_10] = *(int *)(*(int *)(this + 0x4d4) + local_10 * 4);
        }
        if (iVar1 < iVar2) {
          local_40 = local_30 + 1;
          piVar5[local_40] = *(int *)(this + 0x4e0);
        }
        if (local_40 == local_44) {
          for (local_10 = 1; local_10 <= local_40; local_10 = local_10 + 1) {
            iVar1 = piVar5[local_10];
            iVar2 = piVar4[local_10];
            if (local_c < iVar1 - iVar2) {
              iS1((RdrOut *)param_2,piVar4[local_10]);
              BandStat::bbgn((BandStat *)param_2,piVar5[local_10]);
              local_c = iVar1 - iVar2;
            }
          }
          free_ivector(piVar4,1,local_2c + 1);
          free_ivector(piVar5,1,local_30 + 1);
        }
      }
    }
  }
  return;
}

//===== 0x100228b8 =====

/* private: void __thiscall RdrOut::pickcuts(char const *) */

void __thiscall RdrOut::pickcuts(RdrOut *this,char *param_1)

{
  char cVar1;
  int iVar2;
  undefined4 uVar3;
  double *pdVar4;
  int *piVar5;
  size_t sVar6;
  BandStatArray *pBVar7;
  QualCtrl *pQVar8;
  SSNODE *pSVar9;
  char *_Str;
  int iVar10;
  float fVar11;
  double dVar12;
  double dVar13;
  int local_b0;
  SW local_90 [60];
  int local_54;
  int local_50;
  char *local_4c;
  int local_48;
  int local_44;
  int local_40;
  int local_3c;
  SSNODE local_38 [20];
  int local_24;
  int local_20;
  int local_1c;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x228b8  300  ?pickcuts@RdrOut@@AAEXPBD@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_100371eb;
  local_10 = ExceptionList;
  local_20 = 0;
  ExceptionList = &local_10;
  iVar2 = Wvfm::annotate((Wvfm *)(this + 0x1c));
  *(int *)(this + 0x4e0) = iVar2;
  dVar12 = log((double)*(int *)(this + 0x4e0));
  dVar13 = log(2.0);
  dVar12 = ceil(dVar12 / dVar13);
  pow(2.0,dVar12);
  uVar3 = ftol();
  *(undefined4 *)(this + 0x4dc) = uVar3;
  pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
  *(double **)(this + 0x4c0) = pdVar4;
  pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
  *(double **)(this + 0x4c4) = pdVar4;
  pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
  *(double **)(this + 0x4c8) = pdVar4;
  pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
  *(double **)(this + 0x4cc) = pdVar4;
  pdVar4 = dvector(1,*(int *)(this + 0x4dc) << 1);
  *(double **)(this + 0x4d0) = pdVar4;
  piVar5 = ivector(1,*(long *)(this + 0x4e0));
  *(int **)(this + 0x4d4) = piVar5;
  piVar5 = ivector(1,*(long *)(this + 0x4e0));
  *(int **)(this + 0x4d8) = piVar5;
  local_18 = 1;
  for (local_14 = 1; local_14 < *(int *)(this + 0x4e0) * 2; local_14 = local_14 + 2) {
    fVar11 = BandStatArray::qual((BandStatArray *)(this + 0x1c),local_18 + -1);
    *(double *)(*(int *)(this + 0x4c0) + local_14 * 8) = (double)fVar11;
    iVar2 = *(int *)(this + 0x4c0);
    *(undefined4 *)(iVar2 + 8 + local_14 * 8) = 0;
    *(undefined4 *)(iVar2 + 0xc + local_14 * 8) = 0;
    local_18 = local_18 + 1;
  }
  for (; local_14 <= *(int *)(this + 0x4dc) * 2; local_14 = local_14 + 1) {
    iVar2 = *(int *)(this + 0x4c0);
    *(undefined4 *)(iVar2 + local_14 * 8) = 0;
    *(undefined4 *)(iVar2 + 4 + local_14 * 8) = 0;
  }
  dfour1(*(double **)(this + 0x4c0),*(ulong *)(this + 0x4dc),1);
  for (local_1c = 0; local_1c < 7; local_1c = local_1c + 1) {
    for (local_14 = 1; local_14 < *(int *)(this + 0x4e0) * 2; local_14 = local_14 + 2) {
      *(double *)(*(int *)(this + 0x4c4) + local_14 * 8) =
           (double)*(float *)(&DAT_10038bf0 + local_1c * 4);
      iVar2 = *(int *)(this + 0x4c4);
      *(undefined4 *)(iVar2 + 8 + local_14 * 8) = 0;
      *(undefined4 *)(iVar2 + 0xc + local_14 * 8) = 0;
    }
    for (; local_14 <= *(int *)(this + 0x4dc) * 2; local_14 = local_14 + 1) {
      iVar2 = *(int *)(this + 0x4c4);
      *(undefined4 *)(iVar2 + local_14 * 8) = 0;
      *(undefined4 *)(iVar2 + 4 + local_14 * 8) = 0;
    }
    dfour1(*(double **)(this + 0x4c4),*(ulong *)(this + 0x4dc),1);
    for (local_24 = 0; local_24 < 5; local_24 = local_24 + 1) {
      SSNODE::SSNODE(local_38);
      local_8 = 0;
      BandStat::insr((BandStat *)local_38,*(int *)(&DAT_10038bf0 + local_1c * 4));
      cutoff(this,local_24,local_38);
      SSNODE::rdlen(local_38);
      local_3c = ftol();
      if (local_20 < local_3c) {
        local_20 = local_3c;
        QualCtrl::cutdata((QualCtrl *)(this + 0x330),local_38);
      }
      local_8 = 0xffffffff;
      BandStat::~BandStat((BandStat *)local_38);
    }
  }
  free_dvector(*(double **)(this + 0x4c0),1,*(int *)(this + 0x4dc) << 1);
  *(undefined4 *)(this + 0x4c0) = 0;
  free_dvector(*(double **)(this + 0x4c8),1,*(int *)(this + 0x4dc) << 1);
  *(undefined4 *)(this + 0x4c8) = 0;
  free_dvector(*(double **)(this + 0x4c4),1,*(int *)(this + 0x4dc) << 1);
  *(undefined4 *)(this + 0x4c4) = 0;
  free_dvector(*(double **)(this + 0x4cc),1,*(int *)(this + 0x4dc) << 1);
  *(undefined4 *)(this + 0x4cc) = 0;
  free_dvector(*(double **)(this + 0x4d0),1,*(int *)(this + 0x4dc) << 1);
  *(undefined4 *)(this + 0x4d0) = 0;
  free_ivector(*(int **)(this + 0x4d4),1,*(long *)(this + 0x4e0));
  *(undefined4 *)(this + 0x4d4) = 0;
  free_ivector(*(int **)(this + 0x4d8),1,*(long *)(this + 0x4e0));
  *(undefined4 *)(this + 0x4d8) = 0;
  if (param_1 != (char *)0x0) {
    sVar6 = strlen(param_1);
    local_44 = sVar6 << 1;
    pBVar7 = bandstat(this);
    local_40 = Wvfm::annotate((Wvfm *)pBVar7);
    local_b0 = local_40;
    if (local_44 < local_40) {
      local_b0 = local_44;
    }
    local_48 = local_b0;
    pQVar8 = qualctrl(this);
    pSVar9 = QualCtrl::cutdata(pQVar8);
    iVar2 = Annotate::getNumCurrFix((Annotate *)pSVar9);
    if ((iVar2 < local_48) && (local_4c = operator_new(local_48 + 1), local_4c != (char *)0x0)) {
      for (local_50 = 0; local_50 < local_48; local_50 = local_50 + 1) {
        iVar2 = local_50;
        pBVar7 = bandstat(this);
        cVar1 = BandStatArray::call(pBVar7,iVar2);
        local_4c[local_50] = cVar1;
      }
      local_4c[local_50] = '\0';
      SW::SW(local_90,param_1,local_4c);
      local_8 = 1;
      pQVar8 = qualctrl(this);
      pSVar9 = QualCtrl::cutdata(pQVar8);
      local_54 = Annotate::getNumCurrFix((Annotate *)pSVar9);
      iVar2 = SW::hcoord(local_90);
      if (local_54 < iVar2) {
        _Str = SW::hout(local_90);
        sVar6 = strlen(_Str);
        if (3 < (int)sVar6) {
          iVar2 = SW::score(local_90);
          iVar10 = SW::score(local_90);
          if (4 < (iVar10 * iVar2) / (int)sVar6) {
            iVar2 = local_54;
            pQVar8 = qualctrl(this);
            pSVar9 = QualCtrl::cutdata(pQVar8);
            SSNODE::SWold(pSVar9,iVar2);
            iVar2 = SW::hcoord(local_90);
            iVar2 = iVar2 + 1;
            pQVar8 = qualctrl(this);
            pSVar9 = QualCtrl::cutdata(pQVar8);
            iS1((RdrOut *)pSVar9,iVar2);
          }
        }
      }
      operator_delete(local_4c);
      local_8 = 0xffffffff;
      SW::~SW(local_90);
    }
  }
  ExceptionList = local_10;
  return;
}

//===== 0x10023042 =====

/* public: void __thiscall RdrOut::Beautify(int,int,int,int,int) */

void __thiscall
RdrOut::Beautify(RdrOut *this,int param_1,int param_2,int param_3,int param_4,int param_5)

{
  Annotate *this_00;
  int iVar1;
  
                    /* 0x23042  57  ?Beautify@RdrOut@@QAEXHHHHH@Z */
  this_00 = Wvfm::getAnnotation((Wvfm *)(this + 0x28));
  if ((param_5 == 1) || (iVar1 = Wvfm::annotate((Wvfm *)(this + 0x28)), iVar1 == 1)) {
    xOverCut(this,param_5);
  }
  if (param_1 == 1) {
    flatten_(this);
  }
  if (param_2 == 1) {
    minNegSwing_(this);
  }
  if (((param_3 == 1) && (param_4 == 0)) && (resize(this), this_00 != (Annotate *)0x0)) {
    iVar1 = Wvfm::rows((Wvfm *)(this + 0x28));
    Annotate::setNScnl(this_00,6,iVar1);
  }
  if ((param_4 & 3U) == 1) {
    phredify(this);
    if (this_00 != (Annotate *)0x0) {
      iVar1 = Wvfm::rows((Wvfm *)(this + 0x28));
      Annotate::setNScnl(this_00,7,iVar1);
    }
  }
  else if ((param_4 & 3U) == 2) {
    phredify2(this,9,0xf);
    if (this_00 != (Annotate *)0x0) {
      iVar1 = Wvfm::rows((Wvfm *)(this + 0x28));
      Annotate::setNScnl(this_00,7,iVar1);
    }
  }
  else if (((param_4 & 3U) == 3) && (phredify2(this,10,0xc), this_00 != (Annotate *)0x0)) {
    iVar1 = Wvfm::rows((Wvfm *)(this + 0x28));
    Annotate::setNScnl(this_00,7,iVar1);
  }
  return;
}

//===== 0x10023166 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall RdrOut::flatten_(void) */

void __thiscall RdrOut::flatten_(RdrOut *this)

{
  int iVar1;
  int iVar2;
  ulong uVar3;
  double *pdVar4;
  double *pdVar5;
  double dVar6;
  double dVar7;
  double local_30;
  int local_14;
  int local_10;
  uint local_8;
  
                    /* 0x23166  162  ?flatten_@RdrOut@@AAEXXZ */
  iVar1 = Wvfm::endi((Wvfm *)(this + 0x28));
  iVar2 = Wvfm::bgni((Wvfm *)(this + 0x28));
  dVar6 = log((double)((iVar1 - iVar2) + 0x81));
  dVar7 = log(2.0);
  dVar6 = ceil(dVar6 / dVar7);
  pow(2.0,dVar6);
  uVar3 = ftol();
  pdVar4 = dvector(1,uVar3 << 1);
  pdVar5 = dvector(1,uVar3 << 1);
  for (local_8 = 1; (int)local_8 <= (int)(uVar3 * 2); local_8 = local_8 + 1) {
    *(undefined4 *)(pdVar4 + local_8) = 0;
    *(undefined4 *)((int)pdVar4 + local_8 * 8 + 4) = 0;
    *(undefined4 *)(pdVar5 + local_8) = 0;
    *(undefined4 *)((int)pdVar5 + local_8 * 8 + 4) = 0;
  }
  local_14 = 1;
  local_8 = Wvfm::bgni((Wvfm *)(this + 0x28));
  for (; local_14 <= ((iVar1 - iVar2) + 1) * 2; local_14 = local_14 + 2) {
    dVar6 = Wvfm::envv((Wvfm *)(this + 0x28),local_8);
    pdVar4[local_14] = dVar6;
    local_8 = local_8 + 1;
  }
  local_10 = uVar3 * 2 + -1;
  local_14 = 1;
  for (local_8 = 1; (int)local_8 < 0x81; local_8 = local_8 + 1) {
    *(undefined4 *)(pdVar5 + local_10) = 0x1fc07f0;
    *(undefined4 *)((int)pdVar5 + local_10 * 8 + 4) = 0x3f7fc07f;
    *(undefined4 *)(pdVar5 + local_14) = 0x1fc07f0;
    *(undefined4 *)((int)pdVar5 + local_14 * 8 + 4) = 0x3f7fc07f;
    local_14 = local_14 + 2;
    local_10 = local_10 + -2;
  }
  *(undefined4 *)(pdVar5 + local_14) = 0x1fc07f0;
  *(undefined4 *)((int)pdVar5 + local_14 * 8 + 4) = 0x3f7fc07f;
  dfour1(pdVar4,uVar3,1);
  dfour1(pdVar5,uVar3,1);
  FUN_10034b00((int)pdVar4,(int)pdVar5,(int)pdVar4,uVar3);
  dfour1(pdVar4,uVar3,-1);
  local_10 = 1;
  local_8 = Wvfm::bgni((Wvfm *)(this + 0x28));
  while( true ) {
    iVar1 = Wvfm::endi((Wvfm *)(this + 0x28));
    if (iVar1 < (int)local_8) break;
    dVar6 = _DAT_10038d18 + pdVar4[local_10];
    for (local_14 = 1; local_14 < 5; local_14 = local_14 + 1) {
      local_30 = Wvfm::sc_la((Wvfm *)(this + 0x28),local_8,local_14);
      local_30 = local_30 * ((double)(int)uVar3 / dVar6);
      if (_DAT_10038d08 < local_30) {
        local_30 = atan(_DAT_10038d20 * local_30);
      }
      Wvfm::sc_la_set((Wvfm *)(this + 0x28),local_8,local_14,local_30);
    }
    local_8 = local_8 + 1;
    local_10 = local_10 + 2;
  }
  free_dvector(pdVar4,1,uVar3 << 1);
  free_dvector(pdVar5,1,uVar3 << 1);
  return;
}

//===== 0x1002346c =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall RdrOut::minNegSwing_(void) */

void __thiscall RdrOut::minNegSwing_(RdrOut *this)

{
  int iVar1;
  int iVar2;
  double dVar3;
  double dVar4;
  undefined4 local_24;
  undefined4 uStack_20;
  int local_1c;
  undefined4 local_18;
  undefined4 uStack_14;
  int local_8;
  
                    /* 0x2346c  281  ?minNegSwing_@RdrOut@@AAEXXZ */
  local_8 = 1;
  while( true ) {
    iVar1 = Wvfm::cols((Wvfm *)(this + 0x28));
    if (iVar1 < local_8) break;
    local_18 = 0;
    uStack_14 = 0;
    iVar1 = Wvfm::bgni((Wvfm *)(this + 0x28));
    iVar2 = Wvfm::endi((Wvfm *)(this + 0x28));
    for (local_1c = iVar1; local_1c <= iVar2; local_1c = local_1c + 1) {
      dVar3 = Wvfm::sc_la((Wvfm *)(this + 0x28),local_1c,local_8);
      if (dVar3 < (double)CONCAT44(uStack_14,local_18)) {
        local_24 = SUB84(dVar3,0);
        local_18 = local_24;
        uStack_20 = (undefined4)((ulonglong)dVar3 >> 0x20);
        uStack_14 = uStack_20;
      }
    }
    if ((double)CONCAT44(uStack_14,local_18) < _DAT_10038d28) {
      dVar3 = _DAT_10038d30 / (double)CONCAT44(uStack_14,local_18);
      for (local_1c = iVar1; local_1c <= iVar2; local_1c = local_1c + 1) {
        dVar4 = Wvfm::sc_la((Wvfm *)(this + 0x28),local_1c,local_8);
        if (dVar4 < _DAT_10038d28) {
          Wvfm::sc_la_mul((Wvfm *)(this + 0x28),local_1c,local_8,dVar3);
        }
      }
    }
    local_8 = local_8 + 1;
  }
  return;
}

//===== 0x1002358a =====

/* private: void __thiscall RdrOut::resize(void) */

void __thiscall RdrOut::resize(RdrOut *this)

{
  ObsInpSpec *pOVar1;
  int iVar2;
  RC_ACTION RVar3;
  BandStatArray *pBVar4;
  
                    /* 0x2358a  339  ?resize@RdrOut@@AAEXXZ */
  pOVar1 = Wvfm::ispec((Wvfm *)(this + 0x28));
  iVar2 = ObsInpSpec::changedBy(pOVar1);
  pOVar1 = Wvfm::ispec((Wvfm *)(this + 0x28));
  RVar3 = ObsInpSpec::action(pOVar1);
  if (RVar3 != 0) {
    if (RVar3 == 1) {
      Wvfm::resize((Wvfm *)(this + 0x28));
      pBVar4 = bandstat(this);
      BandStatArray::upSmpl(pBVar4,iVar2);
    }
    else if (RVar3 == 2) {
      Wvfm::resize((Wvfm *)(this + 0x28));
      pBVar4 = bandstat(this);
      BandStatArray::dnSmpl(pBVar4,iVar2);
    }
  }
  return;
}

//===== 0x10023615 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall RdrOut::xOverCut(int) */

void __thiscall RdrOut::xOverCut(RdrOut *this,int param_1)

{
  bool bVar1;
  double *pdVar2;
  int iVar3;
  int iVar4;
  float fVar5;
  double dVar6;
  int local_168;
  size_t local_164;
  float local_160 [3];
  int aiStack_154 [23];
  float fStack_f8;
  int iStack_f4;
  int local_98;
  float local_94;
  float local_90;
  float local_8c;
  float local_88;
  float local_84;
  float local_7c;
  double local_78;
  float local_70;
  float local_6c;
  float local_68;
  float local_64;
  float local_60;
  int local_5c;
  int local_58;
  int local_54;
  int local_50;
  int local_4c;
  int local_48;
  int local_44;
  int local_40;
  double *local_3c;
  BandStatArray *local_38;
  void *local_34;
  int local_30;
  void *local_2c;
  void *local_28;
  RdrOut *local_24;
  int local_20;
  int local_1c;
  int local_18;
  int local_14;
  int local_10;
  void *local_c;
  double *local_8;
  
                    /* 0x23615  444  ?xOverCut@RdrOut@@AAEXH@Z */
  local_38 = (BandStatArray *)(this + 0x1c);
  local_24 = this + 0x28;
  local_18 = 0;
  local_1c = 0;
  local_c = (void *)0x0;
  local_34 = (void *)0x0;
  local_3c = (double *)0x0;
  local_8 = (double *)0x0;
  local_28 = (void *)0x0;
  local_2c = (void *)0x0;
  local_18 = Wvfm::annotate((Wvfm *)local_38);
  *(int *)(this + 0x4e4) = local_18;
  if (99 < local_18) {
    local_20 = local_18 / 2;
    local_14 = (int)(local_18 + (local_18 >> 0x1f & 7U)) >> 3;
    iVar3 = BandStatArray::posn(local_38,local_20);
    iVar4 = BandStatArray::posn(local_38,local_14);
    local_30 = (iVar3 - iVar4) / (local_20 - local_14) + 1;
    if (local_30 != 0) {
      local_c = operator_new(local_18 << 2);
      local_34 = operator_new(local_18 << 2);
      local_3c = operator_new(local_30 * 0x10 + 8);
      local_8 = operator_new(local_30 * 0x10 + 8);
      local_28 = operator_new(local_18 << 1);
      local_2c = operator_new(local_18 << 2);
      if (((((local_c == (void *)0x0) || (local_34 == (void *)0x0)) || (local_3c == (double *)0x0))
          || ((local_8 == (double *)0x0 || (local_28 == (void *)0x0)))) || (local_2c == (void *)0x0)
         ) {
        if (local_c != (void *)0x0) {
          operator_delete(local_c);
        }
        if (local_34 != (void *)0x0) {
          operator_delete(local_34);
        }
        if (local_3c != (double *)0x0) {
          operator_delete(local_3c);
        }
        if (local_8 != (double *)0x0) {
          operator_delete(local_8);
        }
        if (local_28 != (void *)0x0) {
          operator_delete(local_28);
        }
        if (local_2c != (void *)0x0) {
          operator_delete(local_2c);
        }
      }
      else {
        for (local_10 = 1; local_10 <= local_30 * 2; local_10 = local_10 + 1) {
          local_3c[local_10] = (double)local_10;
        }
        for (local_10 = 1; local_10 < local_18 + -1; local_10 = local_10 + 1) {
          iVar3 = BandStatArray::posn(local_38,local_10);
          local_54 = BandStatArray::posn(local_38,local_10 + -1);
          local_54 = iVar3 - local_54;
          iVar3 = BandStatArray::posn(local_38,local_10 + 1);
          local_4c = BandStatArray::posn(local_38,local_10);
          local_4c = iVar3 - local_4c;
          local_58 = (local_4c + local_54) / 2;
          local_5c = BandStatArray::bbgn(local_38,local_10);
          local_44 = BandStatArray::bend(local_38,local_10);
          local_48 = (local_44 - local_5c) + 1;
          if (((3 < local_58) && (3 < local_48)) &&
             ((local_58 <= local_30 * 2 && (local_48 <= local_30 * 2)))) {
            fVar5 = BandStatArray::hght(local_38,local_10);
            local_78 = (double)(fVar5 / (float)_DAT_10038d38);
            for (local_50 = local_5c; local_50 <= local_44; local_50 = local_50 + 1) {
              local_40 = (local_50 - local_5c) + 1;
              dVar6 = Wvfm::sc_la((Wvfm *)local_24,local_50,1);
              local_8[local_40] = dVar6;
              for (local_98 = 2; pdVar2 = local_8, iVar3 = local_40, local_98 < 5;
                  local_98 = local_98 + 1) {
                dVar6 = Wvfm::sc_la((Wvfm *)local_24,local_50,local_98);
                if (pdVar2[iVar3] < dVar6) {
                  dVar6 = Wvfm::sc_la((Wvfm *)local_24,local_50,local_98);
                  local_8[local_40] = dVar6;
                }
              }
              local_8[local_40] = local_8[local_40] - local_78;
            }
            iVar3 = dquadratic(local_3c,local_8,local_48,&local_8c);
            if (iVar3 != 0) {
              local_68 = local_84;
              local_6c = local_88;
              local_70 = local_8c;
              local_7c = local_88 * local_88 - _DAT_10038d40 * local_84 * local_8c;
              if ((_DAT_10038d44 <= local_7c) && (local_84 < _DAT_10038d44)) {
                fVar5 = -local_88;
                dVar6 = sqrt((double)local_7c);
                local_60 = ((float)dVar6 + fVar5) / (_DAT_10038d48 * local_68);
                fVar5 = -local_6c;
                dVar6 = sqrt((double)local_7c);
                local_64 = (fVar5 - (float)dVar6) / (_DAT_10038d48 * local_68);
                dVar6 = fabs((double)(local_60 - local_64));
                local_94 = (float)dVar6;
                if ((_DAT_10038d44 != local_94) &&
                   ((local_90 = (float)local_58 / local_94, local_90 <= _DAT_10038d48 &&
                    (_DAT_10038d4c <= local_90)))) {
                  *(undefined2 *)((int)local_28 + local_1c * 2) = (undefined2)local_58;
                  *(float *)((int)local_2c + local_1c * 4) = local_94;
                  *(float *)((int)local_c + local_1c * 4) = local_90;
                  *(int *)((int)local_34 + local_1c * 4) = local_10;
                  local_1c = local_1c + 1;
                }
              }
            }
          }
        }
        operator_delete(local_28);
        operator_delete(local_2c);
        if (param_1 == 1) {
          local_164 = 0;
          local_168 = 0;
          bVar1 = false;
          for (local_10 = 0; local_10 < local_1c; local_10 = local_10 + 1) {
            if (local_164 == 0x19) {
              qsort(local_160,0x19,8,FUN_10023e75);
              if (fStack_f8 < _DAT_10038ce8) {
                if ((bVar1) && (local_168 = local_168 + 1, 7 < local_168)) {
                  local_164 = 0;
                  break;
                }
              }
              else {
                bVar1 = true;
                local_168 = 0;
                qsort(local_160,0x19,8,FUN_10023eb7);
                *(int *)(this + 0x4e4) = iStack_f4 + 0xc;
              }
              local_164 = 0;
            }
            local_160[local_164 * 2] = *(float *)((int)local_c + local_10 * 4);
            local_160[local_164 * 2 + 1] = *(float *)((int)local_34 + local_10 * 4);
            local_164 = local_164 + 1;
          }
          if (0xc < (int)local_164) {
            qsort(local_160,local_164,8,FUN_10023e75);
            if (_DAT_10038ce8 <= local_160[((int)local_164 / 2) * 2 + 2]) {
              qsort(local_160,local_164,8,FUN_10023eb7);
              *(int *)(this + 0x4e4) = (int)local_164 / 2 + aiStack_154[((int)local_164 / 2) * 2];
            }
          }
          if (local_18 < *(int *)(this + 0x4e4)) {
            *(int *)(this + 0x4e4) = local_18;
          }
        }
        if (local_c != (void *)0x0) {
          operator_delete(local_c);
        }
        if (local_34 != (void *)0x0) {
          operator_delete(local_34);
        }
        if (local_3c != (double *)0x0) {
          operator_delete(local_3c);
        }
        if (local_8 != (double *)0x0) {
          operator_delete(local_8);
        }
      }
    }
  }
  return;
}

//===== 0x10023e75 =====

undefined4 __cdecl FUN_10023e75(float *param_1,float *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x10023eb7 =====

int __cdecl FUN_10023eb7(int param_1,int param_2)

{
  return *(int *)(param_1 + 4) - *(int *)(param_2 + 4);
}

//===== 0x10023ed9 =====

/* public: int __thiscall RdrOut::avgqual(void)const  */

int __thiscall RdrOut::avgqual(RdrOut *this)

{
  QualCtrl *pQVar1;
  SSNODE *pSVar2;
  int iVar3;
  int iVar4;
  BandStatArray *this_00;
  undefined4 local_8;
  
                    /* 0x23ed9  74  ?avgqual@RdrOut@@QBEHXZ */
  pQVar1 = qualctrl(this);
  pSVar2 = QualCtrl::cutdata(pQVar1);
  iVar3 = Annotate::getNumCurrFix((Annotate *)pSVar2);
  pQVar1 = qualctrl(this);
  pSVar2 = QualCtrl::cutdata(pQVar1);
  iVar4 = SW::alignedLength((SW *)pSVar2);
  this_00 = bandstat(this);
  for (local_8 = iVar3; local_8 < iVar4; local_8 = local_8 + 1) {
    BandStatArray::qual(this_00,local_8);
    ftol();
  }
  iVar3 = ftol((iVar4 - iVar3) + 1);
  return iVar3;
}

//===== 0x10023f85 =====

/* public: int __thiscall RdrOut::percentN(void)const  */

int __thiscall RdrOut::percentN(RdrOut *this)

{
  BandStatArray *this_00;
  QualCtrl *pQVar1;
  SSNODE *pSVar2;
  int iVar3;
  int local_8;
  
                    /* 0x23f85  297  ?percentN@RdrOut@@QBEHXZ */
  this_00 = bandstat(this);
  pQVar1 = qualctrl(this);
  pSVar2 = QualCtrl::cutdata(pQVar1);
  local_8 = Annotate::getNumCurrFix((Annotate *)pSVar2);
  pQVar1 = qualctrl(this);
  pSVar2 = QualCtrl::cutdata(pQVar1);
  iVar3 = SW::alignedLength((SW *)pSVar2);
  for (; local_8 < iVar3; local_8 = local_8 + 1) {
    BandStatArray::call(this_00,local_8);
  }
  iVar3 = ftol();
  return iVar3;
}

//===== 0x10024039 =====

/* public: char const * __thiscall RdrOut::sequence(char *,int)const  */

char * __thiscall RdrOut::sequence(RdrOut *this,char *param_1,int param_2)

{
  char cVar1;
  BandStatArray *this_00;
  int iVar2;
  int local_18;
  int local_8;
  
                    /* 0x24039  353  ?sequence@RdrOut@@QBEPBDPADH@Z */
  this_00 = bandstat(this);
  iVar2 = Wvfm::annotate((Wvfm *)this_00);
  if (iVar2 < param_2) {
    local_18 = Wvfm::annotate((Wvfm *)this_00);
  }
  else {
    local_18 = param_2;
  }
  for (local_8 = 0; local_8 < local_18; local_8 = local_8 + 1) {
    cVar1 = BandStatArray::call(this_00,local_8);
    param_1[local_8] = cVar1;
  }
  param_1[local_8] = '\0';
  return param_1;
}

//===== 0x100240b5 =====

/* public: char const * __thiscall RdrOut::iubcodes(char *,int)const  */

char * __thiscall RdrOut::iubcodes(RdrOut *this,char *param_1,int param_2)

{
  char cVar1;
  BandStatArray *this_00;
  int iVar2;
  int local_18;
  int local_8;
  
                    /* 0x240b5  251  ?iubcodes@RdrOut@@QBEPBDPADH@Z */
  this_00 = bandstat(this);
  iVar2 = Wvfm::annotate((Wvfm *)this_00);
  if (iVar2 < param_2) {
    local_18 = Wvfm::annotate((Wvfm *)this_00);
  }
  else {
    local_18 = param_2;
  }
  for (local_8 = 0; local_8 < local_18; local_8 = local_8 + 1) {
    cVar1 = BandStatArray::iubc(this_00,local_8);
    param_1[local_8] = cVar1;
  }
  param_1[local_8] = '\0';
  return param_1;
}

//===== 0x10024131 =====

/* public: void __thiscall RdrOut::debug(void)const  */

void __thiscall RdrOut::debug(RdrOut *this)

{
  int iVar1;
  int iVar2;
  
                    /* 0x24131  129  ?debug@RdrOut@@QBEXXZ */
  printf(s_RdrOut_at__p_100406e4,this);
  iVar1 = Annotate::getNumCurrFix((Annotate *)this);
  printf(s_oiS1____d_100406f4,iVar1);
  iVar1 = percentN(this);
  iVar2 = avgqual(this);
  printf(s_average_quality____2d____ambig___10040704,iVar2,iVar1);
  QualCtrl::debug((QualCtrl *)(this + 0x330));
  BandStatArray::debug((BandStatArray *)(this + 0x1c));
  Wvfm::debug((Wvfm *)(this + 0x28),(char *)0x0);
  return;
}

//===== 0x100241b0 =====

void FUN_100241b0(undefined4 param_1,undefined4 param_2,int param_3,undefined *param_4)

{
  while (param_3 = param_3 + -1, -1 < param_3) {
    (*(code *)param_4)();
  }
  return;
}

//===== 0x100241e0 =====

int __fastcall FUN_100241e0(int param_1)

{
  return param_1 + 0xc;
}

//===== 0x10024200 =====

/* public: int __thiscall SW::score(void)const  */

int __thiscall SW::score(SW *this)

{
                    /* 0x24200  351  ?score@SW@@QBEHXZ */
  return *(int *)(this + 0x1c);
}

//===== 0x10024220 =====

/* public: int __thiscall SW::vcoord(void)const  */

int __thiscall SW::vcoord(SW *this)

{
                    /* 0x24220  430  ?vcoord@SW@@QBEHXZ */
  return *(int *)(this + 0x30);
}

//===== 0x10024240 =====

/* public: int __thiscall SW::hcoord(void)const  */

int __thiscall SW::hcoord(SW *this)

{
                    /* 0x24240  227  ?hcoord@SW@@QBEHXZ */
  return *(int *)(this + 0x34);
}

//===== 0x10024260 =====

/* public: int __thiscall SSNODE::SWold(void)const  */

int __thiscall SSNODE::SWold(SSNODE *this)

{
                    /* 0x24260  61  ?SWold@SSNODE@@QBEHXZ
                       0x24260  86  ?bend@BandStat@@QBEHXZ
                       0x24260  433  ?vpos0@SW@@QBEHXZ */
  return *(int *)(this + 0xc);
}

//===== 0x10024280 =====

/* public: int __thiscall Annotate::getNumFwhmGapLen(void)const  */

int __thiscall Annotate::getNumFwhmGapLen(Annotate *this)

{
                    /* 0x24280  198  ?getNumFwhmGapLen@Annotate@@QBEHXZ
                       0x24280  233  ?hpos0@SW@@QBEHXZ
                       0x24280  241  ?insr@BandStat@@QBEHXZ */
  return *(int *)(this + 0x10);
}

//===== 0x100242a0 =====

/* public: int __thiscall SW::alignedLength(void)const  */

int __thiscall SW::alignedLength(SW *this)

{
                    /* 0x242a0  66  ?alignedLength@SW@@QBEHXZ
                       0x242a0  82  ?bbgn@BandStat@@QBEHXZ
                       0x242a0  159  ?finish@SSNODE@@QBEHXZ
                       0x242a0  179  ?getCFixSts@Annotate@@QBEHXZ */
  return *(int *)(this + 8);
}

//===== 0x100242c0 =====

/* public: char const * __thiscall SW::concensus(void)const  */

char * __thiscall SW::concensus(SW *this)

{
                    /* 0x242c0  115  ?concensus@SW@@QBEPBDXZ */
  return *(char **)(this + 0x38);
}

//===== 0x100242e0 =====

/* public: char const * __thiscall SW::vout(void)const  */

char * __thiscall SW::vout(SW *this)

{
                    /* 0x242e0  432  ?vout@SW@@QBEPBDXZ */
  return *(char **)(this + 0x20);
}

//===== 0x10024300 =====

/* public: char const * __thiscall SW::hout(void)const  */

char * __thiscall SW::hout(SW *this)

{
                    /* 0x24300  232  ?hout@SW@@QBEPBDXZ */
  return *(char **)(this + 0x24);
}

//===== 0x10024320 =====

/* public: char __thiscall SW::gapchar(void)const  */

char __thiscall SW::gapchar(SW *this)

{
                    /* 0x24320  173  ?gapchar@SW@@QBEDXZ */
  return '*';
}

//===== 0x10024330 =====

/* public: void __thiscall Wvfm::resize(void) */

void __thiscall Wvfm::resize(Wvfm *this)

{
  ObsInpSpec *pOVar1;
  RC_ACTION RVar2;
  int iVar3;
  int iVar4;
  float fVar5;
  LMConvert local_cc [36];
  LMConvert local_a8 [36];
  LMConvert local_84 [36];
  LMConvert local_60 [36];
  float *local_3c;
  int local_38;
  ShftVect local_34 [8];
  int local_2c;
  double **local_28;
  int local_24;
  int local_20;
  int local_1c;
  float *local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x24330  340  ?resize@Wvfm@@QAEXXZ */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003722a;
  local_10 = ExceptionList;
  local_3c = (float *)0x0;
  local_18 = (float *)0x0;
  local_28 = (double **)0x0;
  ExceptionList = &local_10;
  ShftVect::ShftVect(local_34);
  pOVar1 = ispec(this);
  RVar2 = ObsInpSpec::action(pOVar1);
  if (RVar2 != 0) {
    if (RVar2 == 1) {
      pOVar1 = ispec(this);
      local_14 = ObsInpSpec::changedBy(pOVar1);
      local_38 = rows(this);
      local_2c = local_38 * local_14;
      local_1c = local_2c;
      local_28 = dmatrix(1,local_2c,1,4);
      local_3c = vector(1,local_38 + 1);
      for (local_24 = 1; local_24 < 5; local_24 = local_24 + 1) {
        local_20 = 1;
        while (iVar3 = rows(this), local_20 <= iVar3) {
          local_3c[local_20] =
               (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + local_20 * 4) + local_24 * 8);
          local_20 = local_20 + 1;
        }
        local_3c[local_20] =
             (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + -4 + local_20 * 4) + local_24 * 8);
        LMConvert::LMConvert(local_84,local_3c + 1,local_38,local_14,1);
        local_8 = 0;
        for (local_20 = 1; local_20 <= local_1c; local_20 = local_20 + 1) {
          fVar5 = LMConvert::output(local_84,local_20 + -1);
          local_28[local_20][local_24] = (double)fVar5;
        }
        local_8 = 0xffffffff;
        LMConvert::~LMConvert(local_84);
      }
      local_18 = vector(1,local_1c);
      local_20 = 1;
      while (iVar3 = rows(this), local_20 <= iVar3) {
        local_3c[local_20] = *(float *)(*(int *)(this + 0x300) + local_20 * 4);
        local_20 = local_20 + 1;
      }
      local_3c[local_20] = local_3c[local_20 + -1];
      LMConvert::LMConvert(local_60,local_3c + 1,local_38,local_14,1);
      local_8 = 1;
      for (local_20 = 1; local_20 <= local_1c; local_20 = local_20 + 1) {
        fVar5 = LMConvert::output(local_60,local_20 + -1);
        local_18[local_20] = fVar5;
      }
      iVar3 = local_1c;
      iVar4 = bgni(this);
      pm(this,local_28,local_18,local_1c,iVar4,iVar3);
      envelope(this,local_34);
      free_vector(local_3c,1,local_38);
      local_8 = 0xffffffff;
      LMConvert::~LMConvert(local_60);
    }
    else if (RVar2 == 2) {
      pOVar1 = ispec(this);
      local_14 = ObsInpSpec::changedBy(pOVar1);
      local_38 = rows(this);
      local_2c = local_38 / local_14;
      local_1c = local_2c;
      local_28 = dmatrix(1,local_2c,1,4);
      local_3c = vector(1,local_38 + 1);
      for (local_24 = 1; local_24 < 5; local_24 = local_24 + 1) {
        local_20 = 1;
        while (iVar3 = rows(this), local_20 <= iVar3) {
          local_3c[local_20] =
               (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + local_20 * 4) + local_24 * 8);
          local_20 = local_20 + 1;
        }
        local_3c[local_20] =
             (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + -4 + local_20 * 4) + local_24 * 8);
        LMConvert::LMConvert(local_cc,local_3c + 1,local_38,1,local_14);
        local_8 = 2;
        for (local_20 = 1; local_20 <= local_1c; local_20 = local_20 + 1) {
          fVar5 = LMConvert::output(local_cc,local_20 + -1);
          local_28[local_20][local_24] = (double)fVar5;
        }
        local_8 = 0xffffffff;
        LMConvert::~LMConvert(local_cc);
      }
      local_18 = vector(1,local_1c);
      local_20 = 1;
      while (iVar3 = rows(this), local_20 <= iVar3) {
        local_3c[local_20] = *(float *)(*(int *)(this + 0x300) + local_20 * 4);
        local_20 = local_20 + 1;
      }
      local_3c[local_20] = local_3c[local_20 + -1];
      LMConvert::LMConvert(local_a8,local_3c + 1,local_38,local_14,1);
      local_8 = 3;
      for (local_20 = 1; local_20 <= local_1c; local_20 = local_20 + 1) {
        fVar5 = LMConvert::output(local_a8,local_20 + -1);
        local_18[local_20] = fVar5;
      }
      iVar3 = local_1c;
      iVar4 = bgni(this);
      pm(this,local_28,local_18,local_1c,iVar4,iVar3);
      envelope(this,local_34);
      free_vector(local_3c,1,local_38);
      local_8 = 0xffffffff;
      LMConvert::~LMConvert(local_a8);
    }
  }
  ExceptionList = local_10;
  return;
}

//===== 0x1002488f =====

void FUN_1002488f(void)

{
  FUN_10024899();
  return;
}

//===== 0x10024899 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10024899(void)

{
  _DAT_10042388 = acos(-1.0);
  return;
}

//===== 0x100248c0 =====

undefined4 * __fastcall FUN_100248c0(undefined4 *param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037265;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *param_1 = 0;
  param_1[1] = 0;
  param_1[2] = 0;
  ShftVect::ShftVect((ShftVect *)(param_1 + 3));
  BandStatArray::BandStatArray((BandStatArray *)(param_1 + 5));
  local_8 = 0;
  FUN_10036a10(param_1 + 7,0x14,0x800,FUN_10026600);
  local_8 = CONCAT31(local_8._1_3_,1);
  param_1[0x2a07] = 0;
  fprintf((FILE *)(_iob_exref + 0x40),s__s__d_10040804,s_C__Program_Files_DevStudio_MyPro_100407c8,
          0x11);
  ExceptionList = local_10;
  return param_1;
}

//===== 0x1002497b =====

undefined4 * __thiscall FUN_1002497b(void *this,undefined4 param_1,int param_2)

{
  void *this_00;
  undefined4 *local_20;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003729f;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 1;
  *(undefined4 *)((int)this + 4) = param_1;
  *(undefined4 *)((int)this + 8) = 0;
  ShftVect::ShftVect((ShftVect *)((int)this + 0xc));
  BandStatArray::BandStatArray((BandStatArray *)((int)this + 0x14));
  local_8 = 0;
  FUN_10036a10((int)this + 0x1c,0x14,0x800,FUN_10026600);
  local_8._0_1_ = 1;
  *(undefined4 *)((int)this + 0xa81c) = 0;
  this_00 = operator_new(0x1c0f0);
  local_8 = CONCAT31(local_8._1_3_,2);
  if (this_00 == (void *)0x0) {
    local_20 = (undefined4 *)0x0;
  }
  else {
    local_20 = FUN_100152a0(this_00,param_2);
  }
  *(undefined4 **)((int)this + 0xa81c) = local_20;
  ExceptionList = local_10;
  return this;
}

//===== 0x10024a62 =====

void __fastcall FUN_10024a62(int param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_100372ce;
  local_10 = ExceptionList;
  local_8 = 1;
  ExceptionList = &local_10;
  if (*(int *)(param_1 + 8) != 0) {
    ExceptionList = &local_10;
    if (*(void **)(param_1 + 8) != (void *)0x0) {
      ExceptionList = &local_10;
      FUN_10019250(*(void **)(param_1 + 8),1);
    }
    *(undefined4 *)(param_1 + 8) = 0;
  }
  if (*(int *)(param_1 + 0xa81c) != 0) {
    if (*(void **)(param_1 + 0xa81c) != (void *)0x0) {
      FUN_10026640(*(void **)(param_1 + 0xa81c),1);
    }
    *(undefined4 *)(param_1 + 0xa81c) = 0;
  }
  local_8 = local_8 & 0xffffff00;
  FUN_10036ab0(param_1 + 0x1c,0x14,0x800,BandStat::~BandStat);
  local_8 = 0xffffffff;
  BandStatArray::~BandStatArray((BandStatArray *)(param_1 + 0x14));
  ExceptionList = local_10;
  return;
}

//===== 0x10024b48 =====

undefined4 * __thiscall FUN_10024b48(void *this,undefined4 *param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_100372fd;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  ShftVect::ShftVect((ShftVect *)((int)this + 0xc));
  BandStatArray::BandStatArray((BandStatArray *)((int)this + 0x14));
  local_8 = 0;
  FUN_10036a10((int)this + 0x1c,0x14,0x800,FUN_10026600);
  local_8 = CONCAT31(local_8._1_3_,1);
  *(undefined4 *)((int)this + 0xa81c) = 0;
  FUN_10024bf2(this,param_1);
  ExceptionList = local_10;
  return this;
}

//===== 0x10024bf2 =====

undefined4 * __thiscall FUN_10024bf2(void *this,undefined4 *param_1)

{
  undefined4 uVar1;
  Wvfm *this_00;
  void *this_01;
  undefined4 *local_44;
  undefined4 local_40;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003731d;
  local_10 = ExceptionList;
  if (this != param_1) {
    ExceptionList = &local_10;
    if (*(int *)((int)this + 8) != 0) {
      ExceptionList = &local_10;
      if (*(void **)((int)this + 8) != (void *)0x0) {
        ExceptionList = &local_10;
        FUN_10019250(*(void **)((int)this + 8),1);
      }
      *(undefined4 *)((int)this + 8) = 0;
    }
    if (*(int *)((int)this + 0xa81c) != 0) {
      if (*(void **)((int)this + 0xa81c) != (void *)0x0) {
        FUN_10026640(*(void **)((int)this + 0xa81c),1);
      }
      *(undefined4 *)((int)this + 0xa81c) = 0;
    }
    this_00 = operator_new(0x308);
    local_8 = 0;
    if (this_00 == (Wvfm *)0x0) {
      local_40 = 0;
    }
    else {
      local_40 = Wvfm::Wvfm(this_00,(Wvfm *)param_1[2]);
    }
    local_8 = 0xffffffff;
    *(undefined4 *)((int)this + 8) = local_40;
    this_01 = operator_new(0x1c0f0);
    local_8 = 1;
    if (this_01 == (void *)0x0) {
      local_44 = (undefined4 *)0x0;
    }
    else {
      local_44 = FUN_10015445(this_01,(undefined4 *)param_1[0x2a07]);
    }
    local_8 = 0xffffffff;
    *(undefined4 **)((int)this + 0xa81c) = local_44;
    *(undefined4 *)((int)this + 4) = param_1[1];
    uVar1 = param_1[4];
    *(undefined4 *)((int)this + 0xc) = param_1[3];
    *(undefined4 *)((int)this + 0x10) = uVar1;
    BandStatArray::operator=((BandStatArray *)((int)this + 0x14),(BandStatArray *)(param_1 + 5));
    *(undefined4 *)this = *param_1;
  }
  ExceptionList = local_10;
  return this;
}

//===== 0x10024d90 =====

void __thiscall FUN_10024d90(void *this,Wvfm *param_1)

{
  Wvfm *this_00;
  undefined4 local_2c;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037332;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  if (*(int *)((int)this + 8) != 0) {
    ExceptionList = &local_10;
    if (*(void **)((int)this + 8) != (void *)0x0) {
      ExceptionList = &local_10;
      FUN_10019250(*(void **)((int)this + 8),1);
    }
    *(undefined4 *)((int)this + 8) = 0;
  }
  this_00 = operator_new(0x308);
  local_8 = 0;
  if (this_00 == (Wvfm *)0x0) {
    local_2c = 0;
  }
  else {
    local_2c = Wvfm::Wvfm(this_00,param_1);
  }
  *(undefined4 *)((int)this + 8) = local_2c;
  ExceptionList = local_10;
  return;
}

//===== 0x10024e47 =====

float * __thiscall FUN_10024e47(void *this,Annotate *param_1)

{
  int iVar1;
  float *pfVar2;
  uint uVar3;
  double dVar4;
  int local_8;
  
  iVar1 = Annotate::getCFlen(param_1);
  pfVar2 = vector(1,iVar1);
  if (pfVar2 != (float *)0x0) {
    for (local_8 = 1; local_8 <= iVar1; local_8 = local_8 + 1) {
      uVar3 = FUN_1001bb80(param_1,local_8);
      dVar4 = Wvfm::xbnd(*(Wvfm **)((int)this + 8),uVar3);
      pfVar2[local_8] = (float)dVar4;
    }
  }
  return pfVar2;
}

//===== 0x10024eb8 =====

float * __thiscall FUN_10024eb8(void *this,Annotate *param_1)

{
  int iVar1;
  float *pfVar2;
  uint uVar3;
  float fVar4;
  int local_8;
  
  iVar1 = Annotate::getCFlen(param_1);
  pfVar2 = vector(1,iVar1);
  if (pfVar2 != (float *)0x0) {
    for (local_8 = 1; local_8 <= iVar1; local_8 = local_8 + 1) {
      uVar3 = FUN_1001bb80(param_1,local_8);
      fVar4 = Wvfm::buzz(*(Wvfm **)((int)this + 8),uVar3);
      pfVar2[local_8] = fVar4;
    }
  }
  return pfVar2;
}

//===== 0x10024f29 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __thiscall FUN_10024f29(void *this,int param_1,int param_2,int param_3)

{
  Wvfm *this_00;
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  double dVar5;
  double dVar6;
  int local_24;
  int local_14;
  int local_10;
  int local_8;
  
  this_00 = *(Wvfm **)((int)this + 8);
  local_8 = 1;
  do {
    if (param_3 < local_8) {
      return;
    }
    dVar5 = Wvfm::envv(this_00,*(uint *)(param_1 + local_8 * 4));
    dVar5 = dVar5 / _DAT_10038d60;
    iVar1 = Wvfm::envi(this_00,*(uint *)(param_1 + local_8 * 4));
    local_24 = *(int *)(param_1 + local_8 * 4);
    do {
      local_24 = local_24 + -1;
      if (local_24 < 1) break;
      dVar6 = Wvfm::sc_la(this_00,local_24,iVar1);
    } while (dVar5 < dVar6);
    local_14 = *(int *)(param_1 + local_8 * 4);
    do {
      local_14 = local_14 + 1;
      iVar2 = Wvfm::rows(this_00);
      local_10 = local_8;
      if (iVar2 < local_14) break;
      dVar6 = Wvfm::sc_la(this_00,local_14,iVar1);
    } while (dVar5 < dVar6);
    while ((((local_10 = local_10 + -1, iVar2 = local_8, 0 < local_10 && (local_8 != 1)) &&
            (local_24 <= *(int *)(param_1 + local_10 * 4))) &&
           (iVar3 = Wvfm::envi(this_00,*(uint *)(param_1 + local_10 * 4)), iVar1 == iVar3))) {
      Wvfm::envi(this_00,*(uint *)(param_1 + local_10 * 4));
    }
    while (((local_10 = iVar2 + 1, local_10 <= param_3 && (param_3 != local_8)) &&
           ((*(int *)(param_1 + local_10 * 4) <= local_14 &&
            (iVar2 = Wvfm::envi(this_00,*(uint *)(param_1 + local_10 * 4)), iVar1 == iVar2))))) {
      Wvfm::envi(this_00,*(uint *)(param_1 + local_10 * 4));
      iVar2 = local_10;
    }
    uVar4 = ftol((local_14 - local_24) + 1);
    *(undefined4 *)(param_2 + local_8 * 4) = uVar4;
    local_8 = local_8 + 1;
  } while( true );
}

//===== 0x1002511d =====

undefined4 __thiscall FUN_1002511d(void *this,int param_1,void *param_2)

{
  Wvfm *this_00;
  short sVar1;
  int *piVar2;
  int *piVar3;
  undefined4 uVar4;
  int *piVar5;
  int local_44;
  int local_40;
  int local_3c;
  int local_38;
  int local_2c;
  double local_28;
  double local_1c;
  int local_10;
  int local_c;
  
  local_38 = 0;
  local_10 = 0;
  this_00 = *(Wvfm **)((int)this + 8);
  sVar1 = ShftVect::maxshft((ShftVect *)((int)this + 0xc));
  local_1c = Wvfm::envv(this_00,(int)sVar1 + 1);
  local_28 = Wvfm::envv(this_00,(int)sVar1 + 2);
  piVar2 = ivector(1,param_1);
  piVar3 = ivector(1,param_1);
  if ((piVar2 == (int *)0x0) || (piVar3 == (int *)0x0)) {
    uVar4 = 0;
  }
  else {
    local_2c = 0;
    for (local_c = sVar1 + 2; local_c < param_1; local_c = local_c + 1) {
      if (local_2c == 0) {
        if (local_28 <= local_1c) {
          if (local_28 < local_1c) {
            local_2c = 2;
          }
        }
        else {
          local_2c = 1;
        }
      }
      else if (local_2c == 1) {
        if (local_28 < local_1c) {
          local_2c = 2;
          local_38 = local_38 + 1;
          piVar2[local_38] = local_c + -1;
        }
      }
      else if ((local_2c == 2) && (local_1c < local_28)) {
        local_2c = 1;
        local_10 = local_10 + 1;
        piVar3[local_10] = local_c + -1;
      }
      local_1c = local_28;
      local_28 = Wvfm::envv(this_00,local_c + 1);
    }
    piVar5 = ivector(1,local_38);
    FUN_10024f29(this,(int)piVar2,(int)piVar5,local_38);
    if (1 < local_38) {
      local_40 = 0;
      local_3c = 0;
      local_44 = 0;
      for (local_c = 1; local_c <= local_38; local_c = local_c + 1) {
        local_44 = local_44 + piVar5[local_c];
      }
      for (local_c = 1; local_c <= local_38; local_c = local_c + 1) {
        if (piVar5[local_c] <= ((local_38 / 2 + local_44) / local_38) * 3) {
          local_40 = local_40 + 1;
          piVar2[local_40] = piVar2[local_c];
          piVar5[local_40] = piVar5[local_c];
          if (local_c <= local_10) {
            local_3c = local_3c + 1;
            piVar3[local_3c] = piVar3[local_c];
          }
        }
      }
      if (local_38 < local_10) {
        local_3c = local_3c + 1;
        piVar3[local_3c] = piVar3[local_10];
      }
      local_10 = local_3c;
      local_38 = local_40;
    }
    FUN_1001dee1(param_2,(int)piVar2,local_38,(int)piVar3,local_10,(int)piVar5);
    free_ivector(piVar5,1,local_38);
    free_ivector(piVar2,1,param_1);
    free_ivector(piVar3,1,param_1);
    uVar4 = 1;
  }
  return uVar4;
}

//===== 0x10025431 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __thiscall FUN_10025431(void *this,int param_1,int param_2)

{
  short sVar1;
  ShftVect *this_00;
  int iVar2;
  double dVar3;
  double dVar4;
  undefined4 local_24;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_c;
  
  this_00 = (ShftVect *)FUN_100241e0((int)this);
  sVar1 = ShftVect::maxshft(this_00);
  local_c = (uint)sVar1;
  do {
    local_c = local_c + 1;
    if (param_1 < (int)local_c) {
      return;
    }
    dVar3 = Wvfm::envv(*(Wvfm **)((int)this + 8),local_c);
    dVar3 = dVar3 * _DAT_10038d70;
    local_14 = 0;
    local_10 = 1;
    while (local_14 != 5) {
      iVar2 = Wvfm::cols(*(Wvfm **)((int)this + 8));
      if (iVar2 < local_10) break;
      dVar4 = Wvfm::sc_la(*(Wvfm **)((int)this + 8),local_c,local_10);
      if (dVar3 <= dVar4) {
        if (local_14 == 0) {
          local_24 = local_10;
        }
        else {
          local_24 = 5;
        }
        local_14 = local_24;
      }
      local_10 = local_10 + 1;
    }
    *(int *)(param_2 + local_c * 4) = local_14;
  } while( true );
}

//===== 0x10025506 =====

void FUN_10025506(void)

{
  FUN_10025510();
  return;
}

//===== 0x10025510 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10025510(void)

{
  _DAT_100423f0 = acos(-1.0);
  return;
}

//===== 0x1002552a =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __thiscall
FUN_1002552a(void *this,Annotate *param_1,int param_2,int param_3,uint param_4)

{
  char cVar1;
  char *pcVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  double *pdVar7;
  double *pdVar8;
  double dVar9;
  double dVar10;
  int *piVar11;
  undefined8 uVar12;
  undefined4 local_10c;
  undefined4 local_108;
  float local_100;
  uint local_f0;
  undefined4 local_ec;
  undefined4 uStack_e8;
  int local_e4;
  undefined4 local_e0;
  undefined4 uStack_dc;
  undefined4 local_d0;
  undefined4 uStack_cc;
  float local_c8 [4];
  float local_b8;
  int local_b4;
  double local_b0;
  float local_a8;
  float local_a4;
  float local_a0;
  float local_9c;
  undefined4 local_98;
  undefined4 uStack_94;
  float local_90;
  float local_8c;
  double local_88;
  float local_80 [4];
  uint local_70;
  int local_6c;
  float local_68;
  float local_64;
  double local_60;
  double *local_58;
  double *local_54;
  int local_50;
  int local_4c;
  long local_48;
  int local_44;
  double local_40;
  float *local_38;
  float local_34 [4];
  int *local_24;
  float *local_20;
  double local_1c;
  undefined4 local_14;
  BandStatArray *local_10;
  int local_c;
  int *local_8;
  
  local_c = Annotate::getCFlen(param_1);
  local_8 = (int *)0x0;
  local_24 = (int *)0x0;
  local_14 = 1;
  local_40 = ((double)(param_2 + -1) * _DAT_10038d60 * _DAT_100423f0) / _DAT_10038d78;
  local_1c = _DAT_10038d80 / local_40;
  pcVar2 = SW::hout((SW *)param_1);
  local_48 = (int)(pcVar2 + 1) / 2;
  if ((param_4 & 2) != 0) {
    if (local_48 == 3) {
      local_48 = 4;
    }
    local_54 = dvector(1,local_48);
    local_58 = dvector(1,local_48);
    if ((local_54 == (double *)0x0) || (local_58 == (double *)0x0)) {
      return 0;
    }
    for (local_50 = 1; local_50 <= local_48; local_50 = local_50 + 1) {
      local_54[local_50] = (double)local_50;
      local_60 = (local_54[local_50] - ((double)local_48 + _DAT_10038d80) / _DAT_10038d60) /
                 (local_1c / _DAT_10038d60);
      dVar9 = exp(_DAT_10038d88 * local_60 * local_60);
      local_58[local_50] = dVar9;
    }
    local_4c = dquadratic(local_54,local_58,local_48,local_34);
    free_dvector(local_54,1,local_48);
    free_dvector(local_58,1,local_48);
    if (local_4c != 1) {
      return 0;
    }
  }
  local_8 = ivector(1,local_c);
  if (local_8 == (int *)0x0) {
    *(undefined4 *)this = 2;
    local_14 = 0;
  }
  else {
    piVar11 = local_8;
    iVar5 = local_c;
    iVar3 = SSNODE::SWold((SSNODE *)param_1);
    iVar4 = Annotate::getNumCurrFix(param_1);
    iVar5 = FUN_10019280(iVar4,iVar3,piVar11,iVar5);
    if (iVar5 == 1) {
      local_24 = ivector(1,local_c);
      if (local_24 == (int *)0x0) {
        *(undefined4 *)this = 2;
        free_ivector(local_8,1,local_c);
        local_14 = 0;
      }
      else {
        piVar11 = local_24;
        iVar5 = local_c;
        iVar3 = Annotate::getNumFwhmGapLen(param_1);
        iVar4 = Annotate::getNumCurrFix(param_1);
        iVar5 = FUN_10019280(iVar4,iVar3,piVar11,iVar5);
        if (iVar5 == 1) {
          local_20 = FUN_10024e47(this,param_1);
          if (local_20 == (float *)0x0) {
            *(undefined4 *)this = 2;
            free_ivector(local_8,1,local_c);
            free_ivector(local_24,1,local_c);
            local_14 = 0;
          }
          else {
            local_38 = FUN_10024eb8(this,param_1);
            if (local_38 == (float *)0x0) {
              *(undefined4 *)this = 2;
              free_ivector(local_8,1,local_c);
              free_ivector(local_24,1,local_c);
              free_vector(local_20,1,local_c);
              local_14 = 0;
            }
            else {
              local_10 = (BandStatArray *)FUN_10026690((int)this);
              BandStatArray::init(local_10,local_c);
              for (local_44 = 0; local_44 < local_c; local_44 = local_44 + 1) {
                local_6c = local_44 + 1;
                local_70 = FUN_1001bb80(param_1,local_6c);
                BandStatArray::ntnr(local_10,local_44,local_6c);
                BandStatArray::posn(local_10,local_44,local_70);
                iVar5 = FUN_1001bb60(param_1,local_6c);
                BandStatArray::bbgn(local_10,local_44,iVar5);
                iVar5 = FUN_1001bba0(param_1,local_6c);
                BandStatArray::bend(local_10,local_44,iVar5);
                dVar9 = Wvfm::envv(*(Wvfm **)((int)this + 8),local_70);
                BandStatArray::hght(local_10,local_44,(float)dVar9);
                uVar6 = FUN_1001bb60(param_1,local_6c);
                dVar9 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar6);
                local_64 = (float)dVar9;
                uVar6 = FUN_1001bba0(param_1,local_6c);
                dVar9 = Wvfm::envv(*(Wvfm **)((int)this + 8),uVar6);
                local_68 = (float)dVar9;
                local_100 = local_68;
                if (local_64 < local_68) {
                  local_100 = local_64;
                }
                BandStatArray::lowv(local_10,local_44,local_100);
                BandStatArray::xbnd(local_10,local_44,local_20[local_6c]);
                BandStatArray::buzz(local_10,local_44,local_38[local_6c]);
                iVar5 = FUN_1001bc90(param_1,local_6c);
                BandStatArray::insr(local_10,local_44,iVar5);
                BandStatArray::call(local_10,local_44,*(char *)(param_3 + local_6c));
                if ((param_4 & 2) != 0) {
                  uVar12 = CONCAT44(local_80,(uint)*(byte *)(param_3 + local_6c));
                  iVar5 = FUN_1001bba0(param_1,local_6c);
                  uVar6 = local_70;
                  iVar3 = FUN_1001bb60(param_1,local_6c);
                  cVar1 = FUN_10026133(*(Wvfm **)((int)this + 8),iVar3,uVar6,iVar5,(char)uVar12,
                                       (int)((ulonglong)uVar12 >> 0x20));
                  BandStatArray::iubc(local_10,local_44,cVar1);
                  BandStatArray::squad(local_10,local_44,local_80);
                }
                if ((param_4 & 2) != 0) {
                  local_98 = 0;
                  uStack_94 = 0xbff00000;
                  local_b4 = FUN_1001bcb0(param_1,local_6c);
                  if (4 < local_b4) {
                    local_ec = 0;
                    uStack_e8 = 0x408f4000;
                    local_f0 = FUN_1001bb60(param_1,local_6c);
                    iVar3 = local_f0 + local_b4;
                    iVar5 = Wvfm::rows(*(Wvfm **)((int)this + 8));
                    if (iVar3 < iVar5) {
                      pdVar7 = dvector(1,local_b4);
                      pdVar8 = dvector(1,local_b4);
                      for (local_e4 = 1; local_e4 <= local_b4; local_e4 = local_e4 + 1) {
                        pdVar7[local_e4] = (double)local_e4;
                        dVar9 = Wvfm::envv(*(Wvfm **)((int)this + 8),local_f0);
                        pdVar8[local_e4] = dVar9;
                        if (pdVar8[local_e4] < (double)CONCAT44(uStack_e8,local_ec)) {
                          local_ec = *(undefined4 *)(pdVar8 + local_e4);
                          uStack_e8 = *(undefined4 *)((int)pdVar8 + local_e4 * 8 + 4);
                        }
                        local_f0 = local_f0 + 1;
                      }
                      for (local_e4 = 1; local_e4 <= local_b4; local_e4 = local_e4 + 1) {
                        pdVar8[local_e4] = pdVar8[local_e4] - (double)CONCAT44(uStack_e8,local_ec);
                      }
                      iVar5 = dquadratic(pdVar7,pdVar8,local_b4,local_c8);
                      if (iVar5 != 1) {
                        local_14 = 0;
                        *(undefined4 *)this = 4;
                        break;
                      }
                      dVar9 = corrcoef(local_34,local_c8,4);
                      FUN_100260b5((int)pdVar8,local_b4);
                      iVar5 = dquadratic(pdVar7,pdVar8,local_b4,local_c8);
                      if (iVar5 != 1) {
                        local_14 = 0;
                        *(undefined4 *)this = 4;
                        break;
                      }
                      dVar10 = corrcoef(local_34,local_c8,4);
                      if (dVar9 <= dVar10) {
                        local_e0 = SUB84(dVar10,0);
                        local_10c = local_e0;
                        uStack_dc = (undefined4)((ulonglong)dVar10 >> 0x20);
                        local_108 = uStack_dc;
                      }
                      else {
                        local_d0 = SUB84(dVar9,0);
                        local_10c = local_d0;
                        uStack_cc = (undefined4)((ulonglong)dVar9 >> 0x20);
                        local_108 = uStack_cc;
                      }
                      local_98 = local_10c;
                      uStack_94 = local_108;
                      iVar5 = _isnan((double)CONCAT44(local_108,local_10c));
                      if (iVar5 != 0) {
                        local_98 = 0;
                        uStack_94 = 0xbff00000;
                      }
                      free_dvector(pdVar7,1,local_b4);
                      free_dvector(pdVar8,1,local_b4);
                    }
                    else {
                      local_98 = 0;
                      uStack_94 = 0;
                    }
                  }
                  BandStatArray::shap(local_10,local_44,(float)(double)CONCAT44(uStack_94,local_98))
                  ;
                  iVar5 = FUN_1001bcb0(param_1,local_6c);
                  local_88 = (double)iVar5;
                  local_b0 = (double)local_24[local_6c];
                  BandStatArray::widt(local_10,local_44,
                                      (float)iVar5 / (float)local_24[local_6c] -
                                      (float)_DAT_10038d80);
                  iVar5 = FUN_1001bb60(param_1,local_6c);
                  BandStatArray::bbgn(local_10,local_44,iVar5);
                  iVar5 = FUN_1001bba0(param_1,local_6c);
                  BandStatArray::bend(local_10,local_44,iVar5);
                  local_90 = (float)local_8[local_6c];
                  if (_DAT_10038d90 == local_90) {
                    BandStatArray::lgap(local_10,local_44,0.5);
                    BandStatArray::sgap(local_10,local_44,0.5);
                    local_14 = 0;
                    break;
                  }
                  local_90 = (float)local_8[local_6c];
                  local_a0 = (float)local_8[local_6c] / _DAT_10038d94;
                  local_b8 = local_90 / _DAT_10038d98;
                  iVar5 = FUN_10026670(param_1,local_6c);
                  local_a8 = (float)iVar5;
                  iVar5 = FUN_1001bbc0(param_1,local_6c);
                  local_a4 = (float)iVar5;
                  if (local_a8 <= local_a4) {
                    local_8c = local_a8;
                    local_9c = local_a4;
                  }
                  else {
                    local_9c = local_a8;
                    local_8c = local_a4;
                  }
                  if (local_9c < local_a0) {
                    local_9c = local_b8 - local_9c * local_a0;
                  }
                  if (local_8c < local_a0) {
                    local_8c = local_b8 - local_8c * local_a0;
                  }
                  dVar9 = fmod((double)local_9c,(double)local_90);
                  BandStatArray::lgap(local_10,local_44,(float)dVar9 / local_90);
                  dVar9 = fmod((double)local_8c,(double)local_90);
                  BandStatArray::sgap(local_10,local_44,(float)dVar9 / local_90);
                }
              }
              free_vector(local_38,1,local_c);
              local_38 = (float *)0x0;
              free_vector(local_20,1,local_c);
              local_20 = (float *)0x0;
              free_ivector(local_24,1,local_c);
              local_24 = (int *)0x0;
              free_ivector(local_8,1,local_c);
            }
          }
        }
        else {
          *(undefined4 *)this = 4;
          free_ivector(local_8,1,local_c);
          free_ivector(local_24,1,local_c);
          local_14 = 0;
        }
      }
    }
    else {
      *(undefined4 *)this = 4;
      free_ivector(local_8,1,local_c);
      local_14 = 0;
    }
  }
  return local_14;
}

//===== 0x100260b5 =====

void __cdecl FUN_100260b5(int param_1,int param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 local_c;
  undefined4 local_8;
  
  local_c = param_2;
  for (local_8 = 1; local_8 <= param_2 / 2; local_8 = local_8 + 1) {
    uVar1 = *(undefined4 *)(param_1 + local_8 * 8);
    uVar2 = *(undefined4 *)(param_1 + 4 + local_8 * 8);
    *(undefined4 *)(param_1 + local_8 * 8) = *(undefined4 *)(param_1 + local_c * 8);
    *(undefined4 *)(param_1 + 4 + local_8 * 8) = *(undefined4 *)(param_1 + 4 + local_c * 8);
    *(undefined4 *)(param_1 + local_c * 8) = uVar1;
    *(undefined4 *)(param_1 + 4 + local_c * 8) = uVar2;
    local_c = local_c + -1;
  }
  return;
}

//===== 0x10026133 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

char __cdecl
FUN_10026133(Wvfm *param_1,int param_2,int param_3,int param_4,char param_5,int param_6)

{
  char cVar1;
  char *pcVar2;
  int iVar3;
  double dVar4;
  double dVar5;
  char local_45;
  undefined8 local_38;
  int local_28;
  int local_24;
  undefined4 local_18;
  undefined4 uStack_14;
  int local_10;
  uint local_c;
  
  local_18 = 0xeb1c432d;
  uStack_14 = 0x3f1a36e2;
  local_24 = 0;
  local_c = 0;
  pcVar2 = Wvfm::lnordr(param_1);
  for (local_10 = 1; local_10 < 5; local_10 = local_10 + 1) {
    local_38 = 0.0;
    for (local_28 = param_2; local_28 <= param_4; local_28 = local_28 + 1) {
      dVar4 = Wvfm::sc_la(param_1,local_28,local_10);
      if (_DAT_10038da0 < dVar4) {
        dVar5 = fabs((double)(local_28 - param_3));
        dVar5 = exp(-dVar5 / _DAT_10038d60);
        local_38 = dVar5 * dVar4 + local_38;
      }
    }
    if ((double)CONCAT44(uStack_14,local_18) < local_38) {
      local_18 = (undefined4)local_38;
      uStack_14 = local_38._4_4_;
    }
    *(float *)(param_6 + -4 + local_10 * 4) = (float)local_38;
  }
  local_10 = 1;
  do {
    if (4 < local_10) {
      if ((local_24 == 1) || (local_c == 0)) {
        local_45 = param_5;
      }
      else {
        local_45 = s__TGKCYSBAWRDMHVN_1004080c[local_c];
      }
      return local_45;
    }
    cVar1 = pcVar2[local_10 + -1];
    iVar3 = FUN_1002634a(param_1,local_10,param_2,param_4);
    if (iVar3 == 0) {
      *(undefined4 *)(param_6 + -4 + local_10 * 4) = 0;
    }
    if (param_5 == cVar1) {
LAB_100262ca:
      local_24 = local_24 + 1;
      if (cVar1 == 'A') {
        local_c = local_c | 8;
      }
      else if (cVar1 == 'C') {
        local_c = local_c | 4;
      }
      else if (cVar1 == 'G') {
        local_c = local_c | 2;
      }
      else if (cVar1 == 'T') {
        local_c = local_c | 1;
      }
    }
    else {
      *(float *)(param_6 + -4 + local_10 * 4) =
           *(float *)(param_6 + -4 + local_10 * 4) / (float)(double)CONCAT44(uStack_14,local_18);
      if (((float)_DAT_10038d58 <= *(float *)(param_6 + -4 + local_10 * 4)) && (iVar3 != 0))
      goto LAB_100262ca;
    }
    local_10 = local_10 + 1;
  } while( true );
}

//===== 0x1002634a =====

int __cdecl FUN_1002634a(Wvfm *param_1,int param_2,int param_3,int param_4)

{
  double dVar1;
  double dVar2;
  double dVar3;
  undefined4 local_28;
  undefined4 local_c;
  undefined4 local_8;
  
  local_8 = 0;
  while ((local_c = param_3 + 1, local_8 == 0 && (local_c < param_4))) {
    dVar1 = Wvfm::sc_la(param_1,param_3,param_2);
    dVar2 = Wvfm::sc_la(param_1,local_c,param_2);
    dVar3 = Wvfm::sc_la(param_1,param_3 + 2,param_2);
    if ((dVar2 <= dVar1) || (dVar2 <= dVar3)) {
      local_28 = 0;
    }
    else {
      local_28 = 1;
    }
    local_8 = local_28;
    param_3 = local_c;
  }
  return local_8;
}

//===== 0x100263f4 =====

void __thiscall FUN_100263f4(void *this,int param_1,undefined4 *param_2)

{
  if (param_1 < 1) {
    param_1 = 1;
  }
  else if (0x21 < param_1) {
    param_1 = 0x21;
  }
  *param_2 = *(undefined4 *)(*(int *)((int)this + 0xa81c) + 0x1c064 + param_1 * 4);
  return;
}

//===== 0x10026435 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __thiscall FUN_10026435(void *this,Wvfm *param_1,int param_2,int param_3)

{
  short sVar1;
  int iVar2;
  double dVar3;
  int local_58;
  undefined4 local_54;
  undefined4 uStack_50;
  undefined8 uStack_4c;
  undefined4 local_44;
  undefined4 uStack_40;
  undefined8 uStack_3c;
  int local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  double local_18;
  int local_10;
  Wvfm *local_c;
  int local_8;
  
  local_c = (Wvfm *)FUN_10026690((int)this);
  local_8 = 0;
  while( true ) {
    iVar2 = Wvfm::annotate(local_c);
    if (iVar2 <= local_8) break;
    local_24 = BandStatArray::posn((BandStatArray *)local_c,local_8);
    local_54 = 0;
    uStack_50 = 0xbff00000;
    for (local_10 = 1; iVar2 = local_10, local_58 = local_24, local_10 < 5; local_10 = local_10 + 1)
    {
      *(undefined4 *)(&uStack_4c + local_10) = 0;
      *(undefined4 *)((int)&uStack_4c + iVar2 * 8 + 4) = 0;
      if ((param_3 != 0) && (local_24 <= param_2)) {
        local_58 = local_58 - *(int *)(*(int *)(param_3 + local_10 * 4) + local_24 * 4);
      }
      sVar1 = ShftVect::s((ShftVect *)((int)this + 0xc),local_10);
      local_58 = local_58 - sVar1;
      if ((0 < local_58) && (local_58 < 0x801)) {
        dVar3 = Wvfm::sc_la(param_1,local_58,local_10);
        (&uStack_4c)[local_10] = dVar3;
      }
    }
    local_20 = local_44;
    uStack_1c = uStack_40;
    for (local_10 = 2; local_10 < 5; local_10 = local_10 + 1) {
      if ((double)(&uStack_4c)[local_10] <= (double)CONCAT44(uStack_1c,local_20)) {
        if ((double)CONCAT44(uStack_50,local_54) < (double)(&uStack_4c)[local_10]) {
          local_54 = *(undefined4 *)(&uStack_4c + local_10);
          uStack_50 = *(undefined4 *)((int)&uStack_4c + local_10 * 8 + 4);
        }
      }
      else {
        local_54 = local_20;
        uStack_50 = uStack_1c;
        local_20 = *(undefined4 *)(&uStack_4c + local_10);
        uStack_1c = *(undefined4 *)((int)&uStack_4c + local_10 * 8 + 4);
      }
    }
    if (((double)CONCAT44(uStack_50,local_54) <= _DAT_10038da0) ||
       (_DAT_10038da8 * (double)CONCAT44(uStack_50,local_54) <= (double)CONCAT44(uStack_1c,local_20)
       )) {
      local_18 = 9.9;
    }
    else {
      local_18 = (double)CONCAT44(uStack_1c,local_20) / (double)CONCAT44(uStack_50,local_54);
    }
    BandStatArray::snr((BandStatArray *)local_c,local_8,(float)local_18);
    local_8 = local_8 + 1;
  }
  return;
}

//===== 0x10026600 =====

undefined4 * __fastcall FUN_10026600(undefined4 *param_1)

{
  *param_1 = 0;
  param_1[1] = 0;
  param_1[2] = 0;
  param_1[3] = 0;
  param_1[4] = 0;
  return param_1;
}

//===== 0x10026640 =====

void * __thiscall FUN_10026640(void *this,uint param_1)

{
  FUN_1001543a();
  if ((param_1 & 1) != 0) {
    operator_delete(this);
  }
  return this;
}

//===== 0x10026670 =====

undefined4 __thiscall FUN_10026670(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 0xc) + param_1 * 4);
}

//===== 0x10026690 =====

int __fastcall FUN_10026690(int param_1)

{
  return param_1 + 0x14;
}

//===== 0x100266b0 =====

undefined4 * __cdecl FUN_100266b0(undefined4 *param_1,Wvfm *param_2,ShftVect *param_3)

{
  undefined1 local_28 [24];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037349;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  FUN_10027178(local_28,param_3);
  local_8 = 0;
  FUN_10027a70(local_28,param_1,param_2);
  local_8 = 0xffffffff;
  FUN_100273ca((int)local_28);
  ExceptionList = local_10;
  return param_1;
}

//===== 0x1002670e =====

undefined4 * __thiscall FUN_1002670e(void *this,undefined4 *param_1)

{
  if (this != param_1) {
    *(undefined4 *)((int)this + 8) = param_1[2];
    *(undefined4 *)this = *param_1;
    *(undefined4 *)((int)this + 4) = param_1[1];
  }
  return this;
}

//===== 0x10026742 =====

void __fastcall FUN_10026742(undefined4 *param_1)

{
  printf(s_Criterion__val__8_3f_idx__2d_1004086c,*param_1,param_1[1],param_1[2]);
  return;
}

//===== 0x1002676e =====

void FUN_1002676e(void)

{
  FUN_1002677d();
  FUN_1002678c();
  return;
}

//===== 0x1002677d =====

void FUN_1002677d(void)

{
  FUN_100268d7((int *)&DAT_10042418);
  return;
}

//===== 0x1002678c =====

void FUN_1002678c(void)

{
  FUN_10036c80(FUN_1002679e);
  return;
}

//===== 0x1002679e =====

void FUN_1002679e(void)

{
  FUN_10026aea((undefined4 *)&DAT_10042418);
  return;
}

//===== 0x100267ad =====

undefined2 * __fastcall FUN_100267ad(undefined2 *param_1)

{
  param_1[2] = 0;
  param_1[1] = 0;
  *param_1 = 0;
  return param_1;
}

//===== 0x100267d5 =====

undefined2 * __thiscall FUN_100267d5(void *this,undefined2 *param_1)

{
  *(undefined2 *)this = *param_1;
  *(undefined2 *)((int)this + 2) = param_1[1];
  *(undefined2 *)((int)this + 4) = param_1[2];
  return this;
}

//===== 0x1002680d =====

void * __thiscall FUN_1002680d(void *this,void *param_1,undefined2 *param_2)

{
  short local_18;
  short local_16;
  short local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037373;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  FUN_100267d5(&local_18,param_2);
  local_8 = 1;
  local_18 = local_18 + *(short *)this;
  local_16 = local_16 + *(short *)((int)this + 2);
  local_14 = local_14 + *(short *)((int)this + 4);
  FUN_100267d5(param_1,&local_18);
  local_8 = local_8 & 0xffffff00;
  BandStat::~BandStat((BandStat *)&local_18);
  ExceptionList = local_10;
  return param_1;
}

//===== 0x100268a5 =====

void __fastcall FUN_100268a5(short *param_1)

{
  printf(s_TriVect____hd__hd__hd__1004088c,(int)*param_1,(int)param_1[1],(int)param_1[2]);
  return;
}

//===== 0x100268d7 =====

int * __fastcall FUN_100268d7(int *param_1)

{
  int *local_44;
  int local_34;
  int local_30;
  int local_2c;
  int local_28 [4];
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037388;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *param_1 = 0x9d;
  param_1[1] = 0;
  local_14 = 1;
  local_28[3] = *param_1;
  local_44 = operator_new(local_28[3] * 6 + 4);
  local_8 = 0;
  if (local_44 == (int *)0x0) {
    local_44 = (int *)0x0;
  }
  else {
    *local_44 = local_28[3];
    FUN_10036a10(local_44 + 1,6,local_28[3],FUN_100267ad);
    local_44 = local_44 + 1;
  }
  local_8 = 0xffffffff;
  param_1[1] = (int)local_44;
  if (param_1[1] == 0) {
    fprintf((FILE *)(_iob_exref + 0x40),s_TriVects__TriVects___out_of_memo_100408a4);
                    /* WARNING: Subroutine does not return */
    exit(1);
  }
  *(undefined2 *)(param_1[1] + 4) = 0;
  *(undefined2 *)(param_1[1] + 2) = 0;
  *(undefined2 *)param_1[1] = 0;
  for (local_18 = 0; local_18 < 6; local_18 = local_18 + 1) {
    local_28[0] = -*(int *)(&DAT_10038db8 + local_18 * 4);
    local_28[1] = 0;
    local_28[2] = *(undefined4 *)(&DAT_10038db8 + local_18 * 4);
    for (local_2c = 0; local_2c < 3; local_2c = local_2c + 1) {
      for (local_30 = 0; local_30 < 3; local_30 = local_30 + 1) {
        for (local_34 = 0; local_34 < 3; local_34 = local_34 + 1) {
          if (((local_2c != 1) || (local_30 != 1)) || (local_34 != 1)) {
            *(short *)(param_1[1] + local_14 * 6) = (short)local_28[local_2c];
            *(short *)(param_1[1] + 2 + local_14 * 6) = (short)local_28[local_30];
            *(short *)(param_1[1] + 4 + local_14 * 6) = (short)local_28[local_34];
            local_14 = local_14 + 1;
          }
        }
      }
    }
  }
  ExceptionList = local_10;
  return param_1;
}

//===== 0x10026aea =====

void __fastcall FUN_10026aea(undefined4 *param_1)

{
  if (param_1[1] != 0) {
    if ((void *)param_1[1] != (void *)0x0) {
      FUN_10027af0((void *)param_1[1],3);
    }
    param_1[1] = 0;
    *param_1 = 0;
  }
  return;
}

//===== 0x10026b3e =====

void __fastcall FUN_10026b3e(int *param_1)

{
  int local_8;
  
  printf(s_TriVects____p_100408cc,param_1);
  printf(s_len_____ld_100408dc,*param_1);
  for (local_8 = 0; local_8 < *param_1; local_8 = local_8 + 1) {
    FUN_100268a5((short *)(param_1[1] + local_8 * 6));
  }
  return;
}

//===== 0x10026ba4 =====

/* public: __thiscall ShftVect::ShftVect(void) */

ShftVect * __thiscall ShftVect::ShftVect(ShftVect *this)

{
                    /* 0x26ba4  24  ??0ShftVect@@QAE@XZ */
  *(undefined2 *)(this + 6) = 0;
  *(undefined2 *)(this + 4) = 0;
  *(undefined2 *)(this + 2) = 0;
  *(undefined2 *)this = 0;
  return this;
}

//===== 0x10026bd5 =====

/* public: __thiscall ShftVect::ShftVect(short,short,short,short) */

ShftVect * __thiscall
ShftVect::ShftVect(ShftVect *this,short param_1,short param_2,short param_3,short param_4)

{
                    /* 0x26bd5  23  ??0ShftVect@@QAE@FFFF@Z */
  *(short *)this = param_1;
  *(short *)(this + 2) = param_2;
  *(short *)(this + 4) = param_3;
  *(short *)(this + 6) = param_4;
  return this;
}

//===== 0x10026c10 =====

/* public: __thiscall ShftVect::ShftVect(struct TriVect const &) */

ShftVect * __thiscall ShftVect::ShftVect(ShftVect *this,TriVect *param_1)

{
  short local_c;
  short local_8;
  
                    /* 0x26c10  22  ??0ShftVect@@QAE@ABUTriVect@@@Z */
  *(undefined2 *)(this + 6) = 0;
  *(undefined2 *)(this + 4) = *(undefined2 *)(param_1 + 4);
  *(short *)(this + 2) = *(short *)(this + 4) + *(short *)(param_1 + 2);
  *(short *)this = *(short *)(this + 2) + *(short *)param_1;
  local_c = *(short *)this;
  for (local_8 = 1; local_8 < 4; local_8 = local_8 + 1) {
    if (*(short *)(this + local_8 * 2) < local_c) {
      local_c = *(short *)(this + local_8 * 2);
    }
  }
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    *(short *)(this + local_8 * 2) = *(short *)(this + local_8 * 2) - local_c;
  }
  return this;
}

//===== 0x10026ce9 =====

/* public: struct TriVect __thiscall ShftVect::trivec(void)const  */

void * __thiscall ShftVect::trivec(ShftVect *this)

{
  void *in_stack_00000004;
  short local_1c;
  short local_1a;
  short local_18;
  short local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
                    /* 0x26ce9  427  ?trivec@ShftVect@@QBE?AUTriVect@@XZ */
  local_8 = 0xffffffff;
  puStack_c = &LAB_100373b2;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  FUN_100267ad(&local_1c);
  local_8 = 1;
  local_14 = -*(short *)(this + 6);
  local_18 = *(short *)(this + 4) + local_14;
  local_1a = (*(short *)(this + 2) - local_18) + local_14;
  local_1c = ((*(short *)this - local_1a) - local_18) + local_14;
  FUN_100267d5(in_stack_00000004,&local_1c);
  local_8 = local_8 & 0xffffff00;
  BandStat::~BandStat((BandStat *)&local_1c);
  ExceptionList = local_10;
  return in_stack_00000004;
}

//===== 0x10026da2 =====

/* public: short __thiscall ShftVect::maxshft(void)const  */

short __thiscall ShftVect::maxshft(ShftVect *this)

{
  short local_c;
  int local_8;
  
                    /* 0x26da2  275  ?maxshft@ShftVect@@QBEFXZ */
  local_c = *(short *)this;
  for (local_8 = 1; local_8 < 4; local_8 = local_8 + 1) {
    if (local_c < *(short *)(this + local_8 * 2)) {
      local_c = *(short *)(this + local_8 * 2);
    }
  }
  return local_c;
}

//===== 0x10026df7 =====

/* public: class ShftVect __thiscall ShftVect::ralt(void)const  */

undefined4 * __thiscall ShftVect::ralt(ShftVect *this)

{
  short sVar1;
  undefined4 *in_stack_00000004;
  undefined4 local_20;
  undefined4 local_1c;
  short local_18;
  short local_14;
  short local_10;
  short local_c;
  short local_8;
  
                    /* 0x26df7  325  ?ralt@ShftVect@@QBE?AV1@XZ */
  sVar1 = *(short *)this;
  FUN_100186e0();
  local_8 = ftol();
  local_8 = sVar1 + -2 + local_8;
  sVar1 = *(short *)(this + 2);
  FUN_100186e0();
  local_14 = ftol();
  local_14 = sVar1 + -2 + local_14;
  sVar1 = *(short *)(this + 4);
  FUN_100186e0();
  local_c = ftol();
  local_c = sVar1 + -2 + local_c;
  sVar1 = *(short *)(this + 6);
  FUN_100186e0();
  local_10 = ftol();
  local_10 = sVar1 + -2 + local_10;
  local_18 = local_8;
  if (local_14 < local_8) {
    local_18 = local_14;
  }
  if (local_c < local_18) {
    local_18 = local_c;
  }
  if (local_10 < local_18) {
    local_18 = local_10;
  }
  ShftVect((ShftVect *)&local_20,local_8 - local_18,local_14 - local_18,local_c - local_18,
           local_10 - local_18);
  *in_stack_00000004 = local_20;
  in_stack_00000004[1] = local_1c;
  return in_stack_00000004;
}

//===== 0x10026f18 =====

/* public: void __thiscall ShftVect::debug(int)const  */

void __thiscall ShftVect::debug(ShftVect *this,int param_1)

{
                    /* 0x26f18  132  ?debug@ShftVect@@QBEXH@Z */
  printf(s_ShftVect____p__100408ec,this);
  printf(s_s_____hd__hd__hd__hd__100408fc,(int)*(short *)this,(int)*(short *)(this + 2),
         (int)*(short *)(this + 4),(int)*(short *)(this + 6));
  return;
}

//===== 0x10026f64 =====

int * __thiscall FUN_10026f64(void *this,int param_1)

{
  int iVar1;
  int *local_34;
  void *local_30;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_100373d2;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(int *)this = param_1;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0xc) = 0;
  *(int *)((int)this + 0x10) = *(int *)this + -1;
  *(undefined4 *)((int)this + 0x14) = 0;
  iVar1 = *(int *)this;
  local_30 = operator_new(iVar1 << 3);
  local_8 = 0;
  if (local_30 == (void *)0x0) {
    local_30 = (void *)0x0;
  }
  else {
    FUN_100241b0(local_30,8,iVar1,ShftVect::ShftVect);
  }
  local_8 = 0xffffffff;
  *(void **)((int)this + 4) = local_30;
  iVar1 = *(int *)this;
  local_34 = operator_new(iVar1 * 0x10 + 4);
  local_8 = 1;
  if (local_34 == (int *)0x0) {
    local_34 = (int *)0x0;
  }
  else {
    *local_34 = iVar1;
    FUN_10036a10(local_34 + 1,0x10,iVar1,FUN_10027b50);
    local_34 = local_34 + 1;
  }
  local_8 = 0xffffffff;
  *(int **)((int)this + 8) = local_34;
  if ((*(int *)((int)this + 4) != 0) && (*(int *)((int)this + 8) != 0)) {
    memset(*(void **)((int)this + 8),0,*(int *)this << 4);
    ExceptionList = local_10;
    return this;
  }
  fprintf((FILE *)(_iob_exref + 0x40),s_ShftVects__ShftVects__ld__out_of_10040914,
          *(undefined4 *)this);
                    /* WARNING: Subroutine does not return */
  exit(1);
}

//===== 0x100270fd =====

void FUN_100270fd(void)

{
  FUN_10027107();
  return;
}

//===== 0x10027107 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10027107(void)

{
  _DAT_10042460 = acos(-1.0);
  return;
}

//===== 0x10027121 =====

undefined4 * __thiscall FUN_10027121(void *this,int *param_1)

{
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0xc) = 0;
  *(undefined4 *)((int)this + 0x10) = 0;
  *(undefined4 *)((int)this + 0x14) = 0;
  FUN_1002743d(this,param_1);
  return this;
}

//===== 0x10027178 =====

int * __thiscall FUN_10027178(void *this,ShftVect *param_1)

{
  int iVar1;
  void *this_00;
  TriVect *pTVar2;
  BandStat *pBVar3;
  BandStat *pBVar4;
  int *local_50;
  void *local_4c;
  BandStat local_44 [8];
  int *local_3c;
  int *local_38;
  void *local_34;
  void *local_30;
  undefined4 local_2c;
  undefined4 local_28;
  int local_24;
  int local_20;
  BandStat local_1c [8];
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  int local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037404;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0x9d;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0xc) = 0;
  *(undefined4 *)((int)this + 0x10) = 0x9c;
  *(undefined4 *)((int)this + 0x14) = 0;
  ShftVect::trivec(param_1);
  local_8 = 0;
  local_20 = *(int *)this;
  local_30 = operator_new(local_20 << 3);
  local_8._0_1_ = 1;
  if (local_30 == (void *)0x0) {
    local_4c = (void *)0x0;
  }
  else {
    FUN_100241b0(local_30,8,local_20,ShftVect::ShftVect);
    local_4c = local_30;
  }
  local_34 = local_4c;
  local_8._0_1_ = 0;
  *(void **)((int)this + 4) = local_4c;
  local_24 = *(int *)this;
  local_38 = operator_new(local_24 * 0x10 + 4);
  local_8._0_1_ = 2;
  if (local_38 == (int *)0x0) {
    local_50 = (int *)0x0;
  }
  else {
    *local_38 = local_24;
    FUN_10036a10(local_38 + 1,0x10,local_24,FUN_10027b50);
    local_50 = local_38 + 1;
  }
  local_3c = local_50;
  local_8 = (uint)local_8._1_3_ << 8;
  *(int **)((int)this + 8) = local_50;
  if ((*(int *)((int)this + 4) != 0) && (*(int *)((int)this + 8) != 0)) {
    memset(*(void **)((int)this + 8),0,*(int *)this << 4);
    for (local_14 = 0; local_14 < *(int *)this; local_14 = local_14 + 1) {
      pBVar4 = local_1c;
      pBVar3 = local_44;
      this_00 = (void *)FUN_10027bf0(&DAT_10042418,local_14);
      pTVar2 = FUN_1002680d(this_00,pBVar3,(undefined2 *)pBVar4);
      local_8._0_1_ = 3;
      ShftVect::ShftVect((ShftVect *)&local_2c,pTVar2);
      local_8 = (uint)local_8._1_3_ << 8;
      BandStat::~BandStat(local_44);
      iVar1 = *(int *)((int)this + 4);
      *(undefined4 *)(iVar1 + local_14 * 8) = local_2c;
      *(undefined4 *)(iVar1 + 4 + local_14 * 8) = local_28;
      *(int *)(*(int *)((int)this + 8) + 8 + local_14 * 0x10) = local_14;
      iVar1 = *(int *)((int)this + 8);
      *(undefined4 *)(iVar1 + local_14 * 0x10) = 0;
      *(undefined4 *)(iVar1 + 4 + local_14 * 0x10) = 0;
    }
    local_8 = 0xffffffff;
    BandStat::~BandStat(local_1c);
    ExceptionList = local_10;
    return this;
  }
  fprintf((FILE *)(_iob_exref + 0x40),s_ShftVects__ShftVects_ShftVect___o_10040940);
                    /* WARNING: Subroutine does not return */
  exit(1);
}

//===== 0x100273ca =====

void __fastcall FUN_100273ca(int param_1)

{
  if (*(int *)(param_1 + 4) != 0) {
    operator_delete(*(void **)(param_1 + 4));
    *(undefined4 *)(param_1 + 4) = 0;
  }
  if (*(int *)(param_1 + 8) != 0) {
    if (*(void **)(param_1 + 8) != (void *)0x0) {
      FUN_10027b90(*(void **)(param_1 + 8),3);
    }
    *(undefined4 *)(param_1 + 8) = 0;
  }
  return;
}

//===== 0x1002743d =====

int * __thiscall FUN_1002743d(void *this,int *param_1)

{
  int iVar1;
  undefined4 uVar2;
  int *local_48;
  void *local_44;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037424;
  local_10 = ExceptionList;
  if (this != param_1) {
    ExceptionList = &local_10;
    if (*(int *)((int)this + 4) != 0) {
      ExceptionList = &local_10;
      operator_delete(*(void **)((int)this + 4));
      *(undefined4 *)((int)this + 4) = 0;
    }
    if (*(int *)((int)this + 8) != 0) {
      if (*(void **)((int)this + 8) != (void *)0x0) {
        FUN_10027b90(*(void **)((int)this + 8),3);
      }
      *(undefined4 *)((int)this + 8) = 0;
    }
    *(int *)this = *param_1;
    iVar1 = *(int *)this;
    local_44 = operator_new(iVar1 << 3);
    local_8 = 0;
    if (local_44 == (void *)0x0) {
      local_44 = (void *)0x0;
    }
    else {
      FUN_100241b0(local_44,8,iVar1,ShftVect::ShftVect);
    }
    local_8 = 0xffffffff;
    *(void **)((int)this + 4) = local_44;
    iVar1 = *(int *)this;
    local_48 = operator_new(iVar1 * 0x10 + 4);
    local_8 = 1;
    if (local_48 == (int *)0x0) {
      local_48 = (int *)0x0;
    }
    else {
      *local_48 = iVar1;
      FUN_10036a10(local_48 + 1,0x10,iVar1,FUN_10027b50);
      local_48 = local_48 + 1;
    }
    local_8 = 0xffffffff;
    *(int **)((int)this + 8) = local_48;
    if ((*(int *)((int)this + 4) == 0) || (*(int *)((int)this + 8) == 0)) {
      fprintf((FILE *)(_iob_exref + 0x40),s_ShftVects__operator__out_of_memo_10040970);
                    /* WARNING: Subroutine does not return */
      exit(1);
    }
    memset(*(void **)((int)this + 8),0,*(int *)this << 4);
    for (local_14 = 0; local_14 < *(int *)this; local_14 = local_14 + 1) {
      uVar2 = *(undefined4 *)(param_1[1] + 4 + local_14 * 8);
      iVar1 = *(int *)((int)this + 4);
      *(undefined4 *)(iVar1 + local_14 * 8) = *(undefined4 *)(param_1[1] + local_14 * 8);
      *(undefined4 *)(iVar1 + 4 + local_14 * 8) = uVar2;
      FUN_1002670e((void *)(*(int *)((int)this + 8) + local_14 * 0x10),
                   (undefined4 *)(param_1[2] + local_14 * 0x10));
    }
    *(int *)((int)this + 0xc) = param_1[3];
    *(int *)((int)this + 0x10) = param_1[4];
    *(int *)((int)this + 0x14) = param_1[5];
  }
  ExceptionList = local_10;
  return this;
}

//===== 0x10027694 =====

void __thiscall FUN_10027694(void *this,Wvfm *param_1)

{
  double dVar1;
  undefined4 local_8;
  
  for (local_8 = *(int *)((int)this + 0xc); local_8 <= *(int *)((int)this + 0x10);
      local_8 = local_8 + 1) {
    *(int *)(*(int *)((int)this + 8) + 8 + local_8 * 0x10) = local_8;
    dVar1 = Wvfm::sumEnvLite(param_1,(ShftVect *)(*(int *)((int)this + 4) + local_8 * 8),299,0x6a2);
    *(double *)(*(int *)((int)this + 8) + local_8 * 0x10) = dVar1;
  }
  return;
}

//===== 0x10027705 =====

void __thiscall FUN_10027705(void *this,int param_1)

{
  int local_8;
  
  printf(s_ShftVects____p_10040998,this);
  printf(s_len_____ld_100409a8,*(undefined4 *)this);
  for (local_8 = 0; local_8 < *(int *)this; local_8 = local_8 + 1) {
    printf(s__ld_100409b8,local_8);
    ShftVect::debug((ShftVect *)(*(int *)((int)this + 4) + local_8 * 8),param_1);
    FUN_10026742((undefined4 *)(*(int *)((int)this + 8) + local_8 * 0x10));
  }
  printf(s_mxi____ld_mni____ld_loops___ld_100409c0,*(undefined4 *)((int)this + 0x10),
         *(undefined4 *)((int)this + 0xc),*(undefined4 *)((int)this + 0x14));
  return;
}

//===== 0x100277b9 =====

void __thiscall FUN_100277b9(void *this,int param_1)

{
  int iVar1;
  undefined4 uVar2;
  int iVar3;
  int local_2c;
  int local_28;
  int local_24;
  undefined4 local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037437;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  FUN_10026f64(&local_2c,param_1);
  local_8 = 0;
  local_18 = *(undefined4 *)((int)this + 0x14);
  qsort(*(void **)((int)this + 8),*(size_t *)this,0x10,FUN_100278cf);
  for (local_14 = 0; local_14 < param_1; local_14 = local_14 + 1) {
    iVar3 = (*(int *)this - param_1) + local_14;
    iVar1 = *(int *)(*(int *)((int)this + 8) + 8 + iVar3 * 0x10);
    uVar2 = *(undefined4 *)(*(int *)((int)this + 4) + 4 + iVar1 * 8);
    *(undefined4 *)(local_28 + local_14 * 8) = *(undefined4 *)(*(int *)((int)this + 4) + iVar1 * 8);
    *(undefined4 *)(local_28 + 4 + local_14 * 8) = uVar2;
    iVar3 = iVar3 * 0x10;
    iVar1 = *(int *)((int)this + 8);
    *(undefined4 *)(local_24 + local_14 * 0x10) = *(undefined4 *)(iVar1 + iVar3);
    *(undefined4 *)(local_24 + 4 + local_14 * 0x10) = *(undefined4 *)(iVar1 + 4 + iVar3);
    *(int *)(local_24 + 8 + local_14 * 0x10) = local_14;
  }
  FUN_1002743d(this,&local_2c);
  local_8 = 0xffffffff;
  FUN_100273ca((int)&local_2c);
  ExceptionList = local_10;
  return;
}

//===== 0x100278cf =====

undefined4 __cdecl FUN_100278cf(double *param_1,double *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x1002791d =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __fastcall FUN_1002791d(int *param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  undefined4 *puVar5;
  undefined4 local_28;
  int local_8;
  
  param_1[4] = 0;
  param_1[3] = 0;
  for (local_8 = 1; local_8 < *param_1; local_8 = local_8 + 1) {
    uVar1 = *(undefined4 *)(param_1[2] + local_8 * 0x10);
    uVar2 = *(undefined4 *)(param_1[2] + 4 + local_8 * 0x10);
    if (*(double *)(param_1[2] + param_1[4] * 0x10) <= (double)CONCAT44(uVar2,uVar1)) {
      param_1[4] = local_8;
    }
    if ((double)CONCAT44(uVar2,uVar1) <= *(double *)(param_1[2] + param_1[3] * 0x10)) {
      param_1[3] = local_8;
    }
  }
  puVar5 = (undefined4 *)ShftVect::ralt((ShftVect *)(param_1[1] + param_1[4] * 8));
  uVar1 = puVar5[1];
  iVar3 = param_1[3];
  iVar4 = param_1[1];
  *(undefined4 *)(iVar4 + iVar3 * 8) = *puVar5;
  *(undefined4 *)(iVar4 + 4 + iVar3 * 8) = uVar1;
  if (_DAT_10038dd8 == *(double *)(param_1[2] + param_1[4] * 0x10)) {
    local_28 = 1;
  }
  else if (((_DAT_10038de0 <
             *(double *)(param_1[2] + param_1[3] * 0x10) /
             *(double *)(param_1[2] + param_1[4] * 0x10)) && (0x31 < param_1[5])) ||
          (100 < param_1[5])) {
    local_28 = 1;
  }
  else {
    local_28 = 0;
  }
  return local_28;
}

//===== 0x10027a70 =====

undefined4 * __thiscall FUN_10027a70(void *this,undefined4 *param_1,Wvfm *param_2)

{
  undefined4 uVar1;
  int iVar2;
  
  while( true ) {
    FUN_10027694(this,param_2);
    *(int *)((int)this + 0x14) = *(int *)((int)this + 0x14) + 1;
    if (*(int *)((int)this + 0x14) == 1) {
      FUN_100277b9(this,0x19);
    }
    iVar2 = FUN_1002791d(this);
    if (iVar2 != 0) break;
    *(undefined4 *)((int)this + 0x10) = *(undefined4 *)((int)this + 0xc);
  }
  uVar1 = *(undefined4 *)(*(int *)((int)this + 4) + 4 + *(int *)((int)this + 0x10) * 8);
  *param_1 = *(undefined4 *)(*(int *)((int)this + 4) + *(int *)((int)this + 0x10) * 8);
  param_1[1] = uVar1;
  return param_1;
}

//===== 0x10027af0 =====

BandStat * __thiscall FUN_10027af0(void *this,uint param_1)

{
  if ((param_1 & 2) == 0) {
    BandStat::~BandStat(this);
    if ((param_1 & 1) != 0) {
      operator_delete(this);
    }
  }
  else {
    FUN_10036ab0(this,6,*(int *)((int)this + -4),BandStat::~BandStat);
    operator_delete((void *)((int)this + -4));
  }
  return this;
}

//===== 0x10027b50 =====

undefined4 * __fastcall FUN_10027b50(undefined4 *param_1)

{
  *param_1 = 0;
  param_1[1] = 0;
  param_1[2] = 0;
  return param_1;
}

//===== 0x10027b80 =====

/* public: __thiscall BandStat::~BandStat(void) */

void __thiscall BandStat::~BandStat(BandStat *this)

{
                    /* 0x27b80  31  ??1BandStat@@QAE@XZ
                       0x27b80  39  ??1SSNODE@@QAE@XZ */
  return;
}

//===== 0x10027b90 =====

BandStat * __thiscall FUN_10027b90(void *this,uint param_1)

{
  if ((param_1 & 2) == 0) {
    BandStat::~BandStat(this);
    if ((param_1 & 1) != 0) {
      operator_delete(this);
    }
  }
  else {
    FUN_10036ab0(this,0x10,*(int *)((int)this + -4),BandStat::~BandStat);
    operator_delete((void *)((int)this + -4));
  }
  return this;
}

//===== 0x10027bf0 =====

int __thiscall FUN_10027bf0(void *this,int param_1)

{
  return param_1 * 6 + *(int *)((int)this + 4);
}

//===== 0x10027c10 =====

void FUN_10027c10(int param_1)

{
  float **ppfVar1;
  float **ppfVar2;
  int local_1c;
  int local_18;
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037450;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  ppfVar1 = matrix(1,4,1,4);
  ppfVar2 = matrix(1,4,1,1);
  for (local_1c = 1; local_1c < 5; local_1c = local_1c + 1) {
    ppfVar2[local_1c][1] = 1.0;
    for (local_18 = 1; local_18 < 5; local_18 = local_18 + 1) {
      ppfVar1[local_1c][local_18] = *(float *)(param_1 + (local_1c + -1) * 0x14 + -4 + local_18 * 4)
      ;
    }
  }
  local_8 = 0;
  FUN_100364a0((int)ppfVar1,4,(int)ppfVar2,1);
  FUN_10027d1c();
  return;
}

//===== 0x10027ce0 =====

undefined * Catch_10027ce0(void)

{
  int unaff_EBP;
  
  **(undefined4 **)(unaff_EBP + -0x2c) = 3;
  *(undefined4 *)(unaff_EBP + -0x24) = 1;
  return &DAT_10027cf6;
}

//===== 0x10027cfe =====

undefined * Catch_10027cfe(void)

{
  int unaff_EBP;
  
  **(undefined4 **)(unaff_EBP + -0x2c) = 4;
  *(undefined4 *)(unaff_EBP + -0x28) = 1;
  return &DAT_10027d14;
}

//===== 0x10027d1c =====

void FUN_10027d1c(void)

{
  int unaff_EBP;
  
  *(undefined4 *)(unaff_EBP + -4) = 0xffffffff;
  *(undefined4 *)(unaff_EBP + -0x18) = 1;
  while (*(int *)(unaff_EBP + -0x18) < 5) {
    *(undefined4 *)(unaff_EBP + -0x14) = 1;
    while (*(int *)(unaff_EBP + -0x14) < 5) {
      *(undefined4 *)
       (*(int *)(unaff_EBP + -0x2c) + (*(int *)(unaff_EBP + -0x18) + -1) * 0x10 + 0x38c +
       *(int *)(unaff_EBP + -0x14) * 4) =
           *(undefined4 *)
            (*(int *)(*(int *)(unaff_EBP + -0x20) + *(int *)(unaff_EBP + -0x18) * 4) +
            *(int *)(unaff_EBP + -0x14) * 4);
      *(int *)(unaff_EBP + -0x14) = *(int *)(unaff_EBP + -0x14) + 1;
    }
    *(int *)(unaff_EBP + -0x18) = *(int *)(unaff_EBP + -0x18) + 1;
  }
  free_matrix(*(float ***)(unaff_EBP + -0x1c),1,4,1,1);
  free_matrix(*(float ***)(unaff_EBP + -0x20),1,4,1,4);
  FUN_10027dd1(*(int *)(unaff_EBP + -0x2c) + 0x390,*(float *)(unaff_EBP + 0xc));
  ExceptionList = *(void **)(unaff_EBP + -0xc);
  return;
}

//===== 0x10027dd1 =====

undefined4 __cdecl FUN_10027dd1(int param_1,float param_2)

{
  float local_10;
  int local_c;
  int local_8;
  
  local_8 = 0;
  while( true ) {
    if (3 < local_8) {
      return 0;
    }
    local_10 = *(float *)(param_1 + local_8 * 4);
    for (local_c = 1; (local_10 < param_2 && (local_c < 4)); local_c = local_c + 1) {
      if (local_10 < *(float *)(param_1 + local_c * 0x10 + local_8 * 4)) {
        local_10 = *(float *)(param_1 + local_c * 0x10 + local_8 * 4);
      }
    }
    if (local_10 < param_2) break;
    local_8 = local_8 + 1;
  }
  return 1;
}

//===== 0x10027e70 =====

int * __thiscall FUN_10027e70(void *this,Wvfm *param_1)

{
  Wvfm *this_00;
  int iVar1;
  Annotate *this_01;
  double **ppdVar2;
  void *pvVar3;
  int iVar4;
  SSTLUT *pSVar5;
  double dVar6;
  Wvfm *local_90;
  int local_74;
  SW local_6c [60];
  int local_30;
  int local_2c;
  Wvfm *local_28;
  int local_24;
  int local_20;
  Wvfm *local_1c;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003746e;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 9;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0x430) = 0;
  *(undefined4 *)((int)this + 0x454) = 0;
  local_18 = Wvfm::bgni(param_1);
  local_24 = Wvfm::endi(param_1);
  memset((void *)((int)this + 0xc),0,900);
  for (local_2c = 0; local_2c < 4; local_2c = local_2c + 1) {
    *(undefined4 *)((int)this + local_2c * 4 + 0x434) = 0;
    *(undefined4 *)((int)this + local_2c * 4 + 0x444) = 0;
    *(undefined4 *)((int)this + local_2c * 0x14 + 0x3e0) = 0;
    *(undefined4 *)((int)this + local_2c * 0x14 + 0x3e4) = 0;
    *(undefined4 *)((int)this + local_2c * 0x14 + 1000) = 0;
    *(undefined4 *)((int)this + local_2c * 0x14 + 0x3ec) = 0;
    *(undefined1 *)((int)this + local_2c * 0x14 + 0x3f0) = 0;
  }
  this_00 = operator_new(0x308);
  local_8 = 0;
  if (this_00 == (Wvfm *)0x0) {
    local_90 = (Wvfm *)0x0;
  }
  else {
    local_90 = (Wvfm *)Wvfm::Wvfm(this_00,param_1);
  }
  local_8 = 0xffffffff;
  local_1c = local_90;
  iVar1 = Wvfm::bgni(param_1);
  Wvfm::bgni(local_1c,iVar1);
  iVar1 = Wvfm::endi(param_1);
  Wvfm::endi(local_1c,iVar1);
  local_28 = local_1c;
  FUN_10013a80(local_6c,local_1c,1);
  local_8 = 1;
  iVar1 = Wvfm::annotate(param_1);
  if (iVar1 != 0) {
    this_01 = Wvfm::getAnnotation(param_1);
    ppdVar2 = Wvfm::pwvfm(param_1);
    Annotate::setTraces(this_01,3,ppdVar2);
  }
  iVar1 = SW::vcoord(local_6c);
  *(int *)((int)this + 4) = iVar1;
  if (*(int *)((int)this + 4) < 0x28) {
    *(undefined4 *)this = 2;
  }
  else {
    FUN_10014175((int)local_6c);
    local_20 = Annotate::getNumFwhmGapLen((Annotate *)local_6c);
    if (local_20 < *(int *)((int)this + 4)) {
      if (local_20 < 0xaf) {
        if (0x77 < *(int *)((int)this + 4)) {
          *(int *)((int)this + 4) = *(int *)((int)this + 4) / 3;
        }
      }
      else {
        *(int *)((int)this + 4) = local_20;
      }
      if (*(int *)((int)this + 4) < local_20) {
        *(int *)((int)this + 4) = local_20;
      }
    }
    if (*(int *)((int)this + 4) < 0x28) {
      *(undefined4 *)this = 2;
    }
    else {
      pvVar3 = operator_new(*(int *)((int)this + 4) * 0x1c);
      *(void **)((int)this + 8) = pvVar3;
      if (*(int *)((int)this + 8) == 0) {
        *(undefined4 *)this = 1;
      }
      else {
        local_14 = 10;
        local_30 = *(int *)((int)this + 4);
        *(int *)((int)this + 4) = local_30 + -10;
        for (local_2c = 0; local_2c < *(int *)((int)this + 4); local_2c = local_2c + 1) {
          for (local_74 = 1; local_74 < 5; local_74 = local_74 + 1) {
            iVar1 = local_74;
            iVar4 = FUN_1002c800(local_6c,local_14 + local_2c);
            dVar6 = Wvfm::sc_la(local_28,iVar4,iVar1);
            FUN_100285b8(this,local_2c,local_74 + -1,(float)dVar6);
          }
        }
        iVar1 = Wvfm::hasSSTPattern(local_28);
        if (iVar1 == 0) {
          iVar1 = FUN_1002a965(this);
          if (iVar1 != 0) {
            *(undefined4 *)this = 9;
            FUN_10028807(this);
            if (*(int *)this == 9) {
              FUN_1002b97b(this,(float *)((int)this + 0x3e0));
              if (*(int *)this != 9) {
                *(undefined4 *)this = 7;
              }
            }
            else {
              *(undefined4 *)this = 7;
            }
          }
        }
        else {
          pSVar5 = Wvfm::sstlut(local_28);
          FUN_1002b97b(this,(float *)pSVar5);
        }
      }
    }
  }
  if ((local_1c != (Wvfm *)0x0) && (local_1c != (Wvfm *)0x0)) {
    FUN_10019250(local_1c,1);
  }
  local_8 = 0xffffffff;
  FUN_10013cdd((int)local_6c);
  ExceptionList = local_10;
  return this;
}

//===== 0x1002830d =====

undefined4 * __thiscall FUN_1002830d(void *this,undefined4 *param_1)

{
  *(undefined4 *)this = 9;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0x430) = 0;
  FUN_10028353(this,param_1);
  return this;
}

//===== 0x10028353 =====

undefined4 * __thiscall FUN_10028353(void *this,undefined4 *param_1)

{
  void *pvVar1;
  int iVar2;
  undefined4 *puVar3;
  undefined4 *puVar4;
  int local_c;
  int local_8;
  
  if (param_1 != this) {
    FUN_1002c2cc((int)this);
    *(undefined4 *)this = *param_1;
    *(undefined4 *)((int)this + 0x430) = param_1[0x10c];
    *(undefined4 *)((int)this + 4) = param_1[1];
    pvVar1 = operator_new(*(int *)((int)this + 4) * 0x1c);
    *(void **)((int)this + 8) = pvVar1;
    *(undefined4 *)((int)this + 0x454) = param_1[0x115];
    for (local_8 = 0; local_8 < *(int *)((int)this + 4); local_8 = local_8 + 1) {
      puVar3 = (undefined4 *)(param_1[2] + local_8 * 0x1c);
      puVar4 = (undefined4 *)(*(int *)((int)this + 8) + local_8 * 0x1c);
      for (iVar2 = 7; iVar2 != 0; iVar2 = iVar2 + -1) {
        *puVar4 = *puVar3;
        puVar3 = puVar3 + 1;
        puVar4 = puVar4 + 1;
      }
    }
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      for (local_c = 0; local_c < 4; local_c = local_c + 1) {
        *(undefined4 *)((int)this + local_c * 4 + local_8 * 0x10 + 0x390) =
             param_1[local_8 * 4 + local_c + 0xe4];
      }
    }
    for (local_8 = 0; local_8 < 0x2d; local_8 = local_8 + 1) {
      puVar3 = param_1 + local_8 * 5 + 3;
      puVar4 = (undefined4 *)((int)this + local_8 * 0x14 + 0xc);
      for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
        *puVar4 = *puVar3;
        puVar3 = puVar3 + 1;
        puVar4 = puVar4 + 1;
      }
    }
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      *(undefined4 *)((int)this + local_8 * 4 + 0x3d0) = param_1[local_8 + 0xf4];
      *(undefined4 *)((int)this + local_8 * 4 + 0x434) = param_1[local_8 + 0x10d];
      *(undefined1 *)((int)this + local_8 * 0x14 + 0x3f0) =
           *(undefined1 *)(param_1 + local_8 * 5 + 0xfc);
      *(undefined4 *)((int)this + local_8 * 4 + 0x444) = param_1[local_8 + 0x111];
      for (local_c = 0; local_c < 4; local_c = local_c + 1) {
        *(undefined4 *)((int)this + local_c * 4 + local_8 * 0x14 + 0x3e0) =
             param_1[local_8 * 5 + local_c + 0xf8];
      }
    }
  }
  return this;
}

//===== 0x10028581 =====

void FUN_10028581(void)

{
  FUN_1002858b();
  return;
}

//===== 0x1002858b =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1002858b(void)

{
  _DAT_100424c8 = acos(-1.0);
  return;
}

//===== 0x100285a5 =====

void __fastcall FUN_100285a5(int param_1)

{
  FUN_1002c2cc(param_1);
  return;
}

//===== 0x100285b8 =====

void __thiscall FUN_100285b8(void *this,int param_1,int param_2,undefined4 param_3)

{
  *(undefined4 *)(*(int *)((int)this + 8) + param_1 * 0x1c + param_2 * 4) = param_3;
  return;
}

//===== 0x100285dc =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_100285dc(float *param_1)

{
  float fVar1;
  float fVar2;
  float fVar3;
  double dVar4;
  float local_18;
  
  fVar2 = *param_1 - param_1[2];
  fVar3 = param_1[1] - param_1[3];
  if (_DAT_10038e04 == fVar3) {
    if (fVar2 < _DAT_10038e04) {
      local_18 = 270.0;
    }
    else {
      local_18 = 90.0;
    }
    param_1[4] = local_18;
  }
  else if (fVar2 < _DAT_10038e04) {
    dVar4 = atan((double)(fVar2 / fVar3));
    fVar1 = (float)(((float10)dVar4 * (float10)_DAT_10038e08) / (float10)_DAT_100424c8);
    if (fVar3 < _DAT_10038e04) {
      param_1[4] = _DAT_10038e10 + fVar1;
    }
    else {
      param_1[4] = _DAT_10038e14 + fVar1;
    }
  }
  else {
    dVar4 = atan((double)(fVar2 / fVar3));
    fVar1 = (float)(((float10)dVar4 * (float10)_DAT_10038e08) / (float10)_DAT_100424c8);
    if (fVar3 < _DAT_10038e04) {
      param_1[4] = _DAT_10038e10 + fVar1;
    }
    else {
      param_1[4] = fVar1;
    }
  }
  dVar4 = sqrt((double)(fVar3 * fVar3 + fVar2 * fVar2));
  param_1[5] = (float)dVar4;
  return;
}

//===== 0x1002871a =====

void FUN_1002871a(float *param_1)

{
  float fVar1;
  int iVar2;
  int iVar3;
  int local_2c;
  float fStack_28;
  int iStack_24;
  float fStack_20;
  undefined1 local_1c [8];
  undefined1 local_14;
  undefined1 local_c;
  int local_8;
  
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    (&iStack_24)[local_8 * 2] = local_8;
    (&fStack_28)[local_8 * 2] = param_1[local_8];
  }
  for (local_8 = 0; local_2c = local_8, local_8 < 4; local_8 = local_8 + 1) {
    while (local_2c = local_2c + 1, local_2c < 4) {
      if ((&fStack_28)[local_2c * 2] < (&fStack_28)[local_8 * 2]) {
        fVar1 = (&fStack_28)[local_8 * 2];
        iVar2 = (&iStack_24)[local_8 * 2];
        iVar3 = (&iStack_24)[local_2c * 2];
        (&fStack_28)[local_8 * 2] = (&fStack_28)[local_2c * 2];
        (&iStack_24)[local_8 * 2] = iVar3;
        (&fStack_28)[local_2c * 2] = fVar1;
        (&iStack_24)[local_2c * 2] = iVar2;
      }
    }
  }
  *(undefined1 *)(param_1 + 6) = local_c;
  *(undefined1 *)((int)param_1 + 0x19) = local_14;
  *(undefined1 *)((int)param_1 + 0x1a) = local_1c[0];
  FUN_100285dc(param_1);
  return;
}

//===== 0x10028807 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_10028807(undefined4 *param_1)

{
  float fVar1;
  float fVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  bool bVar9;
  float *pfVar10;
  int iVar11;
  void *pvVar12;
  uint *puVar13;
  int iVar14;
  undefined4 uVar15;
  uint *puVar16;
  double dVar17;
  float afStackY_1120 [411];
  float afStackY_ab4 [180];
  uint local_7c0;
  uint local_7b8;
  uint local_79c;
  int local_798;
  uint local_794;
  uint local_788;
  uint local_784;
  int local_778;
  int local_770;
  uint local_76c;
  int local_764;
  uint local_760;
  float afStack_720 [16];
  uint local_6e0;
  void *local_6dc;
  int local_6d8;
  uint auStack_6d4 [389];
  int local_c0;
  int **local_bc;
  uint local_b8;
  float afStack_b4 [16];
  float afStack_74 [4];
  uint auStack_64 [24];
  
  for (auStack_6d4[0x16c] = 0; auStack_6d4[0x16c] < 0x3c;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    auStack_6d4[auStack_6d4[0x16c] * 6 + 5] = 0;
    auStack_6d4[auStack_6d4[0x16c] * 6 + 4] = 0;
    auStack_6d4[auStack_6d4[0x16c] * 6 + 3] = 0;
    auStack_6d4[auStack_6d4[0x16c] * 6 + 2] = 0;
    auStack_6d4[auStack_6d4[0x16c] * 6] = 0;
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < 4;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    afStack_74[auStack_6d4[0x16c]] = 0.0;
    afStack_b4[auStack_6d4[0x16c] * 4 + 3] = 0.0;
    afStack_b4[auStack_6d4[0x16c] * 4 + 2] = 0.0;
    afStack_b4[auStack_6d4[0x16c] * 4 + 1] = 0.0;
    afStack_b4[auStack_6d4[0x16c] * 4] = 0.0;
    afStack_720[auStack_6d4[0x16c] * 4 + 3] = 0.0;
    afStack_720[auStack_6d4[0x16c] * 4 + 2] = 0.0;
    afStack_720[auStack_6d4[0x16c] * 4 + 1] = 0.0;
    afStack_720[auStack_6d4[0x16c] * 4] = 0.0;
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < (int)param_1[1];
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    pfVar10 = (float *)(param_1[2] + auStack_6d4[0x16c] * 0x1c);
    FUN_1002871a(pfVar10);
    afStack_74[*(char *)(pfVar10 + 6)] = afStack_74[*(char *)(pfVar10 + 6)] + _DAT_10038e18;
    afStack_b4[*(char *)(pfVar10 + 6) * 4 + (int)*(char *)((int)pfVar10 + 0x19)] =
         afStack_b4[*(char *)(pfVar10 + 6) * 4 + (int)*(char *)((int)pfVar10 + 0x19)] +
         _DAT_10038e18;
    if (_DAT_10038e04 == pfVar10[*(char *)(pfVar10 + 6)]) {
      *param_1 = 2;
      return;
    }
    afStack_720[*(char *)(pfVar10 + 6) * 4 + (int)*(char *)((int)pfVar10 + 0x19)] =
         pfVar10[*(char *)((int)pfVar10 + 0x19)] / pfVar10[*(char *)(pfVar10 + 6)] +
         afStack_720[*(char *)(pfVar10 + 6) * 4 + (int)*(char *)((int)pfVar10 + 0x19)];
  }
  for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < 4;
      auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
    afStack_74[auStack_6d4[0x16a]] = afStack_74[auStack_6d4[0x16a]] / (float)(int)param_1[1];
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < 4;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    if (_DAT_10038e04 != afStack_74[auStack_6d4[0x16c]]) {
      for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < 4;
          auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
        afStack_b4[auStack_6d4[0x16c] * 4 + auStack_6d4[0x16a]] =
             afStack_b4[auStack_6d4[0x16c] * 4 + auStack_6d4[0x16a]] /
             ((float)(int)param_1[1] * afStack_74[auStack_6d4[0x16c]]);
      }
    }
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < 4;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < 4;
        auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
      if (afStack_b4[auStack_6d4[0x16c] * 4 + auStack_6d4[0x16a]] != _DAT_10038e04) {
        afStack_720[auStack_6d4[0x16c] * 4 + auStack_6d4[0x16a]] =
             afStack_720[auStack_6d4[0x16c] * 4 + auStack_6d4[0x16a]] /
             (afStack_b4[auStack_6d4[0x16c] * 4 + auStack_6d4[0x16a]] *
              afStack_74[auStack_6d4[0x16c]] * (float)(int)param_1[1]);
      }
    }
  }
  local_c0 = 0;
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < 4;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    if (_DAT_10038e1c < afStack_74[auStack_6d4[0x16c]]) {
      for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < 4;
          auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
        if ((auStack_6d4[0x16c] != auStack_6d4[0x16a]) &&
           (_DAT_10038e1c < afStack_b4[auStack_6d4[0x16c] * 4 + auStack_6d4[0x16a]])) {
          for (auStack_6d4[0x169] = 0; auStack_6d4[0x169] < 5;
              auStack_6d4[0x169] = auStack_6d4[0x169] + 1) {
            auStack_6d4[local_c0 * 6] = auStack_6d4[0x16c];
            auStack_6d4[local_c0 * 6 + 2] = auStack_6d4[0x16a];
            auStack_6d4[local_c0 * 6 + 1] = auStack_6d4[0x169];
            local_c0 = local_c0 + 1;
          }
        }
      }
    }
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < (int)param_1[1];
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    iVar11 = param_1[2] + auStack_6d4[0x16c] * 0x1c;
    for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < local_c0;
        auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
      if ((((int)*(char *)(iVar11 + 0x18) == auStack_6d4[auStack_6d4[0x16a] * 6]) &&
          ((int)*(char *)(iVar11 + 0x19) == auStack_6d4[auStack_6d4[0x16a] * 6 + 2])) &&
         (*(float *)(iVar11 + *(char *)(iVar11 + 0x19) * 4) /
          *(float *)(iVar11 + *(char *)(iVar11 + 0x18) * 4) <=
          *(float *)(&DAT_10038df0 + auStack_6d4[auStack_6d4[0x16a] * 6 + 1] * 4))) {
        auStack_6d4[auStack_6d4[0x16a] * 6 + 3] = auStack_6d4[auStack_6d4[0x16a] * 6 + 3] + 1;
        break;
      }
    }
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < 4;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < 6;
        auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
      auStack_64[auStack_6d4[0x16c] * 6 + auStack_6d4[0x16a]] = 0;
    }
    for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < local_c0;
        auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
      if (auStack_6d4[auStack_6d4[0x16a] * 6] == auStack_6d4[0x16c]) {
        if ((int)auStack_64[auStack_6d4[0x16c] * 6 + 3] <
            (int)auStack_6d4[auStack_6d4[0x16a] * 6 + 3]) {
          for (auStack_6d4[0x169] = 0; (int)auStack_6d4[0x169] < 6;
              auStack_6d4[0x169] = auStack_6d4[0x169] + 1) {
            auStack_64[auStack_6d4[0x16c] * 6 + auStack_6d4[0x169]] =
                 auStack_6d4[auStack_6d4[0x16a] * 6 + auStack_6d4[0x169]];
          }
          auStack_64[auStack_6d4[0x16c] * 6 + 5] = auStack_6d4[0x16c] + 1;
        }
      }
      else if ((int)auStack_6d4[0x16c] < (int)auStack_6d4[auStack_6d4[0x16a] * 6]) break;
    }
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    auStack_6d4[auStack_6d4[0x16c] * 6 + 3] = auStack_6d4[auStack_6d4[0x16c] * 6 + 3] * 100;
    auStack_6d4[auStack_6d4[0x16c] * 6 + 3] =
         (int)auStack_6d4[auStack_6d4[0x16c] * 6 + 3] / (int)param_1[1];
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < 4;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    auStack_6d4[auStack_6d4[0x16c] * 6 + 0x16d] = 0;
    for (auStack_6d4[0x16a] = 0; auStack_6d4[0x16a] < 5; auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1
        ) {
      auStack_6d4[auStack_6d4[0x16c] * 6 + auStack_6d4[0x16a] + 0x16e] = 0;
    }
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    uVar3 = auStack_6d4[auStack_6d4[0x16c] * 6];
    uVar4 = auStack_6d4[auStack_6d4[0x16c] * 6 + 1];
    uVar5 = auStack_6d4[auStack_6d4[0x16c] * 6 + 3];
    auStack_6d4[uVar3 * 6 + 0x16d] = auStack_6d4[uVar3 * 6 + 0x16d] + uVar5;
    auStack_6d4[uVar3 * 6 + uVar4 + 0x16e] = auStack_6d4[uVar3 * 6 + uVar4 + 0x16e] + uVar5;
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    if ((((1 < (int)auStack_6d4[auStack_6d4[0x16c] * 6 + 1]) ||
         (auStack_6d4[auStack_6d4[0x16c] * 6 + 3] == 0)) ||
        (5 < (int)auStack_6d4[auStack_6d4[auStack_6d4[0x16c] * 6] * 6 + 0x16d] /
             (int)auStack_6d4[auStack_6d4[0x16c] * 6 + 3])) &&
       ((int)auStack_6d4[auStack_6d4[0x16c] * 6 + 3] < 5)) {
      for (auStack_6d4[0x16a] = auStack_6d4[0x16c]; (int)auStack_6d4[0x16a] < local_c0 + -1;
          auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
        for (auStack_6d4[0x169] = 0; (int)auStack_6d4[0x169] < 6;
            auStack_6d4[0x169] = auStack_6d4[0x169] + 1) {
          auStack_6d4[auStack_6d4[0x16a] * 6 + auStack_6d4[0x169]] =
               auStack_6d4[(auStack_6d4[0x16a] + 1) * 6 + auStack_6d4[0x169]];
        }
      }
      local_c0 = local_c0 + -1;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] - 1;
    }
  }
  local_bc = imatrix(1,local_c0,1,local_c0);
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    uVar3 = auStack_6d4[auStack_6d4[0x16c] * 6];
    uVar4 = auStack_6d4[auStack_6d4[0x16c] * 6 + 2];
    uVar5 = auStack_6d4[auStack_6d4[0x16c] * 6 + 1];
    local_bc[auStack_6d4[0x16c] + 1][auStack_6d4[0x16c] + 1] = 0;
    for (auStack_6d4[0x16a] = auStack_6d4[0x16c] + 1; (int)auStack_6d4[0x16a] < local_c0;
        auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
      uVar6 = auStack_6d4[auStack_6d4[0x16a] * 6];
      uVar7 = auStack_6d4[auStack_6d4[0x16a] * 6 + 2];
      uVar8 = auStack_6d4[auStack_6d4[0x16a] * 6 + 1];
      local_bc[auStack_6d4[0x16c] + 1][auStack_6d4[0x16a] + 1] = 4;
      local_bc[auStack_6d4[0x16a] + 1][auStack_6d4[0x16c] + 1] = 0;
      if (((uVar3 == uVar6) && (uVar4 == uVar7)) && (iVar11 = abs(uVar5 - uVar8), iVar11 < 2)) {
        local_bc[auStack_6d4[0x16c] + 1][auStack_6d4[0x16a] + 1] = 1;
      }
      else if ((((uVar3 == uVar7) && (uVar4 == uVar6)) && (3 < uVar5)) && (3 < uVar8)) {
        local_bc[auStack_6d4[0x16c] + 1][auStack_6d4[0x16a] + 1] = 2;
      }
      else {
        if (uVar3 == uVar6) {
          local_7b8 = uVar8;
          if ((int)uVar8 <= (int)uVar5) {
            local_7b8 = uVar5;
          }
          if ((int)local_7b8 < 2) {
            local_bc[auStack_6d4[0x16c] + 1][auStack_6d4[0x16a] + 1] = 3;
            goto LAB_10029472;
          }
        }
        if ((uVar3 == uVar6) && (uVar5 == uVar8)) {
          local_bc[auStack_6d4[0x16c] + 1][auStack_6d4[0x16a] + 1] = 3;
        }
      }
LAB_10029472:
    }
  }
  local_6e0 = 0;
  for (local_6d8 = 1; local_6d8 < 4; local_6d8 = local_6d8 + 1) {
    for (auStack_6d4[0x16c] = 1; (int)auStack_6d4[0x16c] < local_c0;
        auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
      for (auStack_6d4[0x16a] = auStack_6d4[0x16c] + 1; (int)auStack_6d4[0x16a] <= local_c0;
          auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
        if ((local_6d8 == local_bc[auStack_6d4[0x16c]][auStack_6d4[0x16a]]) &&
           (auStack_6d4[(auStack_6d4[0x16c] + -1) * 6 + 4] == 0)) {
          local_6e0 = local_6e0 + 1;
          auStack_6d4[(auStack_6d4[0x16c] + -1) * 6 + 4] = local_6e0;
          if (auStack_6d4[(auStack_6d4[0x16a] - 1) * 6 + 4] == 0) {
            auStack_6d4[(auStack_6d4[0x16a] - 1) * 6 + 4] = local_6e0;
          }
        }
      }
    }
  }
  for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
      auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
    if (auStack_6d4[auStack_6d4[0x16c] * 6 + 4] == 0) {
      local_6e0 = local_6e0 + 1;
      auStack_6d4[auStack_6d4[0x16c] * 6 + 4] = local_6e0;
    }
  }
  free_imatrix(local_bc,1,local_c0,1,local_c0);
  if ((int)local_6e0 < 4) {
    *param_1 = 8;
  }
  else {
    if (4 < (int)local_6e0) {
      pvVar12 = operator_new(local_6e0 * 4 + 4);
      for (auStack_6d4[0x16c] = 1; (int)auStack_6d4[0x16c] <= (int)local_6e0;
          auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
        *(undefined4 *)((int)pvVar12 + auStack_6d4[0x16c] * 4) = 0;
        for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < local_c0;
            auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
          if (auStack_6d4[0x16c] == auStack_6d4[auStack_6d4[0x16a] * 6 + 4]) {
            *(uint *)((int)pvVar12 + auStack_6d4[0x16c] * 4) =
                 *(int *)((int)pvVar12 + auStack_6d4[0x16c] * 4) +
                 auStack_6d4[auStack_6d4[0x16a] * 6 + 3];
          }
        }
      }
      for (; 4 < (int)local_6e0; local_6e0 = local_6e0 - 1) {
        local_764 = 100;
        local_760 = 0;
        for (auStack_6d4[0x16c] = 1; (int)auStack_6d4[0x16c] <= (int)local_6e0;
            auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
          if (*(int *)((int)pvVar12 + auStack_6d4[0x16c] * 4) < local_764) {
            local_760 = auStack_6d4[0x16c];
            local_764 = *(int *)((int)pvVar12 + auStack_6d4[0x16c] * 4);
          }
        }
        for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
            auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
          if (local_760 == auStack_6d4[auStack_6d4[0x16c] * 6 + 4]) {
            for (auStack_6d4[0x16a] = auStack_6d4[0x16c]; (int)auStack_6d4[0x16a] < local_c0 + -1;
                auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
              for (auStack_6d4[0x169] = 0; (int)auStack_6d4[0x169] < 6;
                  auStack_6d4[0x169] = auStack_6d4[0x169] + 1) {
                auStack_6d4[auStack_6d4[0x16a] * 6 + auStack_6d4[0x169]] =
                     auStack_6d4[(auStack_6d4[0x16a] + 1) * 6 + auStack_6d4[0x169]];
              }
            }
            local_c0 = local_c0 + -1;
            auStack_6d4[0x16c] = auStack_6d4[0x16c] - 1;
          }
        }
        for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
            auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
          if ((int)local_760 < (int)auStack_6d4[auStack_6d4[0x16c] * 6 + 4]) {
            auStack_6d4[auStack_6d4[0x16c] * 6 + 4] = auStack_6d4[auStack_6d4[0x16c] * 6 + 4] - 1;
          }
        }
      }
      operator_delete(pvVar12);
    }
    local_6dc = operator_new((local_6e0 + 1) * 0x10);
    for (auStack_6d4[0x16c] = 1; (int)auStack_6d4[0x16c] <= (int)local_6e0;
        auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
      *(undefined4 *)((int)local_6dc + auStack_6d4[0x16c] * 0x10 + 0xc) = 0;
      *(undefined4 *)((int)local_6dc + auStack_6d4[0x16c] * 0x10 + 8) = 0;
      *(undefined4 *)((int)local_6dc + auStack_6d4[0x16c] * 0x10 + 4) = 0;
      *(undefined4 *)((int)local_6dc + auStack_6d4[0x16c] * 0x10) = 0;
    }
    for (auStack_6d4[0x16b] = 1; (int)auStack_6d4[0x16b] <= (int)local_6e0;
        auStack_6d4[0x16b] = auStack_6d4[0x16b] + 1) {
      puVar13 = (uint *)((int)local_6dc + auStack_6d4[0x16b] * 0x10);
      for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
          auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
        if (auStack_6d4[0x16b] == auStack_6d4[auStack_6d4[0x16c] * 6 + 4]) {
          puVar13[2] = puVar13[2] | 1 << ((byte)auStack_6d4[auStack_6d4[0x16c] * 6 + 1] & 0x1f);
          *puVar13 = *puVar13 | 1 << ((byte)auStack_6d4[auStack_6d4[0x16c] * 6] & 0x1f);
          puVar13[1] = puVar13[1] | 1 << ((byte)auStack_6d4[auStack_6d4[0x16c] * 6 + 2] & 0x1f);
        }
      }
    }
    auStack_6d4[0x168] = 0;
    for (auStack_6d4[0x16b] = 1; (int)auStack_6d4[0x16b] <= (int)local_6e0;
        auStack_6d4[0x16b] = auStack_6d4[0x16b] + 1) {
      puVar13 = (uint *)((int)local_6dc + auStack_6d4[0x16b] * 0x10);
      local_770 = 0;
      for (local_76c = 1; (int)local_76c < 9; local_76c = local_76c << 1) {
        if ((*puVar13 & local_76c) != 0) {
          local_770 = local_770 + 1;
        }
      }
      if (local_770 == 1) {
        local_778 = 1;
        for (auStack_6d4[0x16c] = 1; (int)auStack_6d4[0x16c] <= (int)local_6e0;
            auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
          if ((auStack_6d4[0x16c] != auStack_6d4[0x16b]) &&
             ((*puVar13 & *(uint *)((int)local_6dc + auStack_6d4[0x16c] * 0x10)) != 0)) {
            local_778 = local_778 + 1;
          }
        }
        if (local_778 == 1 && (auStack_6d4[0x168] & *puVar13) == 0) {
          puVar13[3] = *puVar13;
          auStack_6d4[0x168] = auStack_6d4[0x168] | *puVar13;
        }
        else {
          bVar9 = true;
          for (auStack_6d4[0x16c] = 1; (bVar9 && ((int)auStack_6d4[0x16c] <= (int)local_6e0));
              auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
            if ((auStack_6d4[0x16c] != auStack_6d4[0x16b]) &&
               ((*puVar13 == *(uint *)((int)local_6dc + auStack_6d4[0x16c] * 0x10) &&
                (*(int *)((int)local_6dc + auStack_6d4[0x16c] * 0x10 + 8) <= (int)puVar13[2])))) {
              bVar9 = false;
            }
          }
          if ((bVar9) && ((auStack_6d4[0x168] & *puVar13) == 0)) {
            puVar13[3] = *puVar13;
            auStack_6d4[0x168] = auStack_6d4[0x168] | *puVar13;
          }
        }
      }
    }
    for (auStack_6d4[0x16b] = 1; (int)auStack_6d4[0x16b] <= (int)local_6e0;
        auStack_6d4[0x16b] = auStack_6d4[0x16b] + 1) {
      puVar13 = (uint *)((int)local_6dc + auStack_6d4[0x16b] * 0x10);
      if (puVar13[3] == 0) {
        local_784 = *puVar13;
        for (auStack_6d4[0x16c] = 1; (int)auStack_6d4[0x16c] <= (int)local_6e0;
            auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
          if (auStack_6d4[0x16c] != auStack_6d4[0x16b]) {
            puVar16 = (uint *)((int)local_6dc + auStack_6d4[0x16c] * 0x10);
            local_788 = *puVar16;
            if (puVar16[3] != 0) {
              local_788 = local_788 & puVar16[3];
            }
            local_784 = local_784 & ~local_788;
          }
        }
        switch(local_784) {
        case 1:
        case 2:
        case 4:
        case 8:
          puVar13[3] = local_784;
        }
      }
    }
    for (auStack_6d4[0x16b] = 1; (int)auStack_6d4[0x16b] <= (int)local_6e0;
        auStack_6d4[0x16b] = auStack_6d4[0x16b] + 1) {
      puVar13 = (uint *)((int)local_6dc + auStack_6d4[0x16b] * 0x10);
      if (puVar13[3] == 0) {
        local_794 = puVar13[1];
        for (auStack_6d4[0x16c] = 1; (int)auStack_6d4[0x16c] <= (int)local_6e0;
            auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
          if ((auStack_6d4[0x16c] != auStack_6d4[0x16b]) &&
             (*(int *)((int)local_6dc + auStack_6d4[0x16c] * 0x10 + 0xc) != 0)) {
            local_794 = local_794 & ~*(uint *)((int)local_6dc + auStack_6d4[0x16c] * 0x10 + 0xc);
          }
        }
        if (local_794 == 0) {
          local_7c0 = *puVar13;
        }
        else {
          local_7c0 = local_794;
        }
        puVar13[3] = local_7c0;
      }
    }
    local_b8 = 0;
    for (auStack_6d4[0x16b] = 1; (int)auStack_6d4[0x16b] <= (int)local_6e0;
        auStack_6d4[0x16b] = auStack_6d4[0x16b] + 1) {
      for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
          auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
        if (auStack_6d4[0x16b] == auStack_6d4[auStack_6d4[0x16c] * 6 + 4]) {
          switch(*(undefined4 *)((int)local_6dc + auStack_6d4[0x16b] * 0x10 + 0xc)) {
          case 1:
            auStack_6d4[auStack_6d4[0x16c] * 6 + 5] = 1;
            break;
          case 2:
            auStack_6d4[auStack_6d4[0x16c] * 6 + 5] = 2;
            break;
          case 4:
            auStack_6d4[auStack_6d4[0x16c] * 6 + 5] = 3;
            break;
          case 8:
            auStack_6d4[auStack_6d4[0x16c] * 6 + 5] = 4;
          }
          if (auStack_6d4[auStack_6d4[0x16c] * 6 + 5] != 0) {
            local_b8 = local_b8 | 1 << ((char)auStack_6d4[auStack_6d4[0x16c] * 6 + 5] - 1U & 0x1f);
          }
        }
      }
    }
    operator_delete(local_6dc);
    if (local_b8 != 0xf) {
      for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < local_c0;
          auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
        if (auStack_6d4[auStack_6d4[0x16c] * 6 + 5] == 0) {
          for (auStack_6d4[0x16a] = auStack_6d4[0x16c] + 1; (int)auStack_6d4[0x16a] < local_c0;
              auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
            for (auStack_6d4[0x169] = 0; (int)auStack_6d4[0x169] < 6;
                auStack_6d4[0x169] = auStack_6d4[0x169] + 1) {
              auStack_6d4[(auStack_6d4[0x16a] + -1) * 6 + auStack_6d4[0x169]] =
                   auStack_6d4[auStack_6d4[0x16a] * 6 + auStack_6d4[0x169]];
            }
          }
          local_c0 = local_c0 + -1;
          auStack_6d4[0x16c] = auStack_6d4[0x16c] + -1;
        }
      }
      for (local_798 = 0; local_798 < 4; local_798 = local_798 + 1) {
        if (((local_b8 & 1 << ((byte)local_798 & 0x1f)) == 0) &&
           (auStack_64[local_798 * 6 + 3] != 0)) {
          for (auStack_6d4[0x169] = 0; (int)auStack_6d4[0x169] < 6;
              auStack_6d4[0x169] = auStack_6d4[0x169] + 1) {
            auStack_6d4[local_c0 * 6 + auStack_6d4[0x169]] =
                 auStack_64[local_798 * 6 + auStack_6d4[0x169]];
          }
          local_c0 = local_c0 + 1;
          local_b8 = local_b8 | 1 << ((byte)local_798 & 0x1f);
        }
      }
      if (local_b8 != 0xf) {
        *param_1 = 8;
        return;
      }
    }
    param_1[0x10c] = 0;
    for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < 4;
        auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
      param_1[auStack_6d4[0x16c] + 0x10d] = 0;
      param_1[auStack_6d4[0x16c] + 0x111] = 0;
      param_1[auStack_6d4[0x16c] * 5 + 0xf8] = 0;
      param_1[auStack_6d4[0x16c] * 5 + 0xf9] = 0;
      param_1[auStack_6d4[0x16c] * 5 + 0xfa] = 0;
      param_1[auStack_6d4[0x16c] * 5 + 0xfb] = 0;
      *(undefined1 *)(param_1 + auStack_6d4[0x16c] * 5 + 0xfc) = 0;
    }
    local_b8 = 0;
    for (auStack_6d4[0x16c] = 0; (int)auStack_6d4[0x16c] < (int)param_1[1];
        auStack_6d4[0x16c] = auStack_6d4[0x16c] + 1) {
      iVar11 = param_1[2] + auStack_6d4[0x16c] * 0x1c;
      fVar1 = *(float *)(iVar11 + *(char *)(iVar11 + 0x19) * 4);
      fVar2 = *(float *)(iVar11 + *(char *)(iVar11 + 0x18) * 4);
      *(undefined1 *)(iVar11 + 0x1b) = 0xff;
      for (auStack_6d4[0x16a] = 0; auStack_6d4[0x16a] < 5;
          auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
        if (fVar1 / fVar2 <= *(float *)(&DAT_10038df0 + auStack_6d4[0x16a] * 4)) {
          local_79c = auStack_6d4[0x16a];
          break;
        }
      }
      for (auStack_6d4[0x16a] = 0; (int)auStack_6d4[0x16a] < local_c0;
          auStack_6d4[0x16a] = auStack_6d4[0x16a] + 1) {
        if (((auStack_6d4[auStack_6d4[0x16a] * 6] == (int)*(char *)(iVar11 + 0x18)) &&
            (auStack_6d4[auStack_6d4[0x16a] * 6 + 2] == (int)*(char *)(iVar11 + 0x19))) &&
           (auStack_6d4[auStack_6d4[0x16a] * 6 + 1] == local_79c)) {
          *(char *)(iVar11 + 0x1b) = (char)auStack_6d4[auStack_6d4[0x16a] * 6 + 5] + -1;
          iVar14 = (int)*(char *)(iVar11 + 0x1b);
          param_1[0x10c] = param_1[0x10c] + 1;
          param_1[*(char *)(iVar11 + 0x1b) + 0x10d] = param_1[*(char *)(iVar11 + 0x1b) + 0x10d] + 1;
          local_b8 = local_b8 | 1 << (*(byte *)(iVar11 + 0x1b) & 0x1f);
          if (*(char *)(param_1 + iVar14 * 5 + 0xfc) == '\0') {
            *(char *)(param_1 + iVar14 * 5 + 0xfc) = (char)auStack_6d4[auStack_6d4[0x16a] * 6 + 5];
            for (auStack_6d4[0x169] = 0; (int)auStack_6d4[0x169] < 4;
                auStack_6d4[0x169] = auStack_6d4[0x169] + 1) {
              param_1[iVar14 * 5 + auStack_6d4[0x169] + 0xf8] =
                   *(float *)(iVar11 + auStack_6d4[0x169] * 4) /
                   *(float *)(iVar11 + *(char *)(iVar11 + 0x18) * 4);
              dVar17 = fabs((double)(float)param_1[iVar14 * 5 + auStack_6d4[0x169] + 0xf8]);
              if (dVar17 <= _DAT_10038e20) {
                param_1[iVar14 * 5 + auStack_6d4[0x169] + 0xf8] = 0;
              }
            }
            uVar15 = ftol();
            param_1[*(char *)(iVar11 + 0x1b) + 0x111] = uVar15;
          }
          break;
        }
      }
    }
    if (local_b8 != 0xf) {
      *param_1 = 8;
    }
  }
  return;
}

//===== 0x1002a904 =====

void __cdecl FUN_1002a904(int param_1,float *param_2,int *param_3)

{
  undefined4 local_8;
  
  *param_3 = 1;
  *param_2 = *(float *)(param_1 + 4);
  for (local_8 = 2; local_8 < 5; local_8 = local_8 + 1) {
    if (*param_2 < *(float *)(param_1 + local_8 * 4)) {
      *param_3 = local_8;
      *param_2 = *(float *)(param_1 + local_8 * 4);
    }
  }
  return;
}

//===== 0x1002a965 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int __fastcall FUN_1002a965(undefined4 *param_1)

{
  double dVar1;
  int iVar2;
  undefined4 uVar3;
  undefined8 local_188;
  float local_17c;
  float local_178 [7];
  float local_15c;
  float local_158;
  float local_154;
  float local_150;
  float local_140;
  float *local_13c;
  double local_138;
  undefined8 local_130;
  int local_128;
  float local_124;
  undefined4 local_120;
  undefined4 uStack_11c;
  float *local_118;
  float **local_114;
  double local_110 [5];
  uint local_e8;
  int *local_e4;
  double *local_e0;
  int local_dc;
  int local_d8;
  undefined8 uStack_d4;
  undefined4 local_cc;
  undefined4 local_c8;
  undefined4 local_c4;
  undefined4 local_c0;
  undefined4 local_bc;
  undefined4 local_b8;
  undefined4 local_b4;
  undefined4 local_b0;
  float **local_ac;
  int local_a8;
  uint local_a4;
  float afStack_a0 [4];
  char acStack_90 [64];
  int local_50 [5];
  int local_3c;
  double local_38 [5];
  float **local_10;
  int local_c;
  int local_8;
  
  local_50[0] = 0;
  local_e0 = (double *)0x0;
  local_e4 = (int *)0x0;
  for (local_c = 0; local_c < 4; local_c = local_c + 1) {
    local_118 = afStack_a0 + local_c * 5;
    local_50[local_c + 1] = 0;
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      local_118[local_8] = 0.0;
    }
  }
  local_114 = matrix(1,param_1[1],1,4);
  local_ac = matrix(1,param_1[1],1,4);
  local_10 = matrix(1,4,1,param_1[1]);
  if (((local_114 == (float **)0x0) || (local_ac == (float **)0x0)) || (local_10 == (float **)0x0))
  {
    if (local_114 != (float **)0x0) {
      free_matrix(local_114,1,param_1[1],1,4);
    }
    if (local_ac != (float **)0x0) {
      free_matrix(local_ac,1,param_1[1],1,4);
    }
    if (local_10 != (float **)0x0) {
      free_matrix(local_10,1,4,1,param_1[1]);
    }
    *param_1 = 1;
    return 1;
  }
  for (local_c = 1; local_c <= (int)param_1[1]; local_c = local_c + 1) {
    for (local_8 = 1; local_8 < 5; local_8 = local_8 + 1) {
      local_114[local_c][local_8] =
           *(float *)(param_1[2] + (local_c + -1) * 0x1c + -4 + local_8 * 4);
    }
  }
  local_50[0] = FUN_1002c30b((int)local_114,local_10,param_1[1]);
  if (local_50[0] == 0) {
    local_e0 = dvector(1,param_1[1]);
    local_e4 = ivector(1,param_1[1]);
    iVar2 = FUN_1002b757((int)local_10,param_1[1],(int)local_e0,(int)local_e4,(int)local_110,
                         (int)local_38);
    if (iVar2 == 0) {
      local_a8 = 0;
      local_e8 = 0;
      local_a4 = 0;
      param_1[0x110] = 0;
      param_1[0x10f] = 0;
      param_1[0x10e] = 0;
      param_1[0x10d] = 0;
      param_1[0x10c] = 0;
      local_b4 = 0;
      local_b0 = 0xbff00000;
      local_bc = 0;
      local_b8 = 0xbff00000;
      local_c4 = 0;
      local_c0 = 0xbff00000;
      local_cc = 0;
      local_c8 = 0xbff00000;
      for (local_c = 1; local_c <= (int)param_1[1]; local_c = local_c + 1) {
        local_3c = local_e4[local_c];
        if (_DAT_10038e30 == local_38[local_3c]) {
          local_188 = 0.0;
        }
        else {
          local_188 = (local_e0[local_c] - local_110[local_3c]) / local_38[local_3c];
        }
        local_120 = (undefined4)local_188;
        uStack_11c = local_188._4_4_;
        if ((_DAT_10038e38 < local_188) && (local_188 <= _DAT_10038e40)) {
          local_a8 = local_a8 + 1;
          param_1[0x10c] = param_1[0x10c] + 1;
          local_114[local_a8][1] = *(float *)(param_1[2] + (local_c + -1) * 0x1c);
          local_114[local_a8][2] = *(float *)(param_1[2] + 4 + (local_c + -1) * 0x1c);
          local_114[local_a8][3] = *(float *)(param_1[2] + 8 + (local_c + -1) * 0x1c);
          local_114[local_a8][4] = *(float *)(param_1[2] + 0xc + (local_c + -1) * 0x1c);
          local_ac[local_a8][4] = 0.0;
          local_ac[local_a8][3] = 0.0;
          local_ac[local_a8][2] = 0.0;
          local_ac[local_a8][1] = 0.0;
          local_ac[local_a8][local_3c] = local_114[local_a8][local_3c];
          FUN_1002a904((int)local_114[local_a8],&local_124,&local_128);
          if (local_128 == local_3c) {
            iVar2 = local_128 + -1;
            local_13c = afStack_a0 + iVar2 * 5;
            acStack_90[iVar2 * 0x14] = (char)local_128;
            *local_13c = *local_13c + local_114[local_a8][1];
            afStack_a0[iVar2 * 5 + 1] = afStack_a0[iVar2 * 5 + 1] + local_114[local_a8][2];
            afStack_a0[iVar2 * 5 + 2] = afStack_a0[iVar2 * 5 + 2] + local_114[local_a8][3];
            afStack_a0[iVar2 * 5 + 3] = afStack_a0[iVar2 * 5 + 3] + local_114[local_a8][4];
            local_50[local_128] = local_50[local_128] + 1;
            local_a4 = local_a4 | 1 << ((char)local_128 - 1U & 0x1f);
          }
          iVar2 = local_3c;
          param_1[local_3c + 0x10c] = param_1[local_3c + 0x10c] + 1;
          local_e8 = local_e8 | 1 << ((char)local_3c - 1U & 0x1f);
          local_138 = -100.0;
          for (local_dc = 1; local_dc < 5; local_dc = local_dc + 1) {
            if ((local_dc != local_3c) && ((float)local_138 < local_10[local_dc][local_c])) {
              local_138 = (double)local_10[local_dc][local_c];
            }
          }
          local_130 = local_e0[local_c] - local_138;
          dVar1 = local_130;
          if ((double)(&uStack_d4)[local_3c] < local_130) {
            *(undefined4 *)(&uStack_d4 + local_3c) = (undefined4)local_130;
            local_130._4_4_ = (undefined4)((ulonglong)local_130 >> 0x20);
            *(undefined4 *)((int)&uStack_d4 + iVar2 * 8 + 4) = local_130._4_4_;
            *(undefined1 *)(param_1 + (local_3c + -1) * 5 + 0xfc) = (undefined1)local_3c;
            local_15c = local_114[local_a8][1];
            param_1[(local_3c + -1) * 5 + 0xf8] = local_15c;
            local_158 = local_114[local_a8][2];
            param_1[(local_3c + -1) * 5 + 0xf9] = local_158;
            local_154 = local_114[local_a8][3];
            param_1[(local_3c + -1) * 5 + 0xfa] = local_154;
            local_150 = local_114[local_a8][4];
            param_1[(local_3c + -1) * 5 + 0xfb] = local_150;
            local_140 = (float)param_1[(local_3c + -1) * 5 + 0xf8];
            for (local_dc = 1; local_dc < 4; local_dc = local_dc + 1) {
              if (local_140 < (float)param_1[(local_3c + -1) * 5 + local_dc + 0xf8]) {
                local_140 = (float)param_1[(local_3c + -1) * 5 + local_dc + 0xf8];
              }
            }
            for (local_dc = 0; local_dc < 4; local_dc = local_dc + 1) {
              param_1[(local_3c + -1) * 5 + local_dc + 0xf8] =
                   (float)param_1[(local_3c + -1) * 5 + local_dc + 0xf8] / local_140;
            }
            local_130 = dVar1;
            FUN_100285dc(&local_15c);
            uVar3 = ftol();
            param_1[local_3c + 0x110] = uVar3;
          }
        }
      }
      *param_1 = 8;
      if (local_e8 == 0xf) {
        local_50[0] = FUN_1002c588(param_1,(int)local_114,(int)local_ac,local_a8);
        if (local_50[0] == 0) {
          local_50[0] = FUN_10027dd1((int)(param_1 + 0xe4),0.7);
          if (local_50[0] == 0) {
            param_1[0x115] = 1;
            *param_1 = 9;
            goto LAB_1002b67a;
          }
        }
        *param_1 = 7;
        local_d8 = 0;
        for (local_c = 0; local_c < 4; local_c = local_c + 1) {
          if (_DAT_10038e18 == (float)param_1[local_c * 6 + 0xf8]) {
            local_d8 = local_d8 + 1;
          }
        }
        if (local_d8 == 4) {
          local_50[0] = FUN_10027c10((int)(param_1 + 0xf8));
          if (local_50[0] == 0) {
            param_1[0x115] = 2;
            *param_1 = 9;
            goto LAB_1002b67a;
          }
        }
      }
      if (local_a4 == 0xf) {
        local_d8 = 0;
        for (local_3c = 0; local_3c < 4; local_3c = local_3c + 1) {
          local_17c = 0.0;
          for (local_dc = 0; local_dc < 4; local_dc = local_dc + 1) {
            afStack_a0[local_3c * 5 + local_dc] =
                 afStack_a0[local_3c * 5 + local_dc] / (float)local_50[local_3c + 1];
            local_178[local_dc] = afStack_a0[local_3c * 5 + local_dc];
            if (local_17c < local_178[local_dc]) {
              local_17c = local_178[local_dc];
            }
          }
          param_1[local_3c + 0x10d] = local_50[local_3c + 1];
          for (local_dc = 0; local_dc < 4; local_dc = local_dc + 1) {
            param_1[local_3c * 5 + local_dc + 0xf8] =
                 afStack_a0[local_3c * 5 + local_dc] / local_17c;
          }
          FUN_100285dc(local_178);
          uVar3 = ftol();
          param_1[local_3c + 0x111] = uVar3;
          if (_DAT_10038e18 == (float)param_1[local_3c * 6 + 0xf8]) {
            local_d8 = local_d8 + 1;
          }
        }
        if ((local_d8 == 4) && (local_50[0] = FUN_10027c10((int)(param_1 + 0xf8)), local_50[0] == 0)
           ) {
          param_1[0x115] = 3;
          *param_1 = 9;
        }
      }
    }
    else {
      *param_1 = 8;
    }
  }
LAB_1002b67a:
  if (local_114 != (float **)0x0) {
    free_matrix(local_114,1,param_1[1],1,4);
  }
  if (local_ac != (float **)0x0) {
    free_matrix(local_ac,1,param_1[1],1,4);
  }
  if (local_10 != (float **)0x0) {
    free_matrix(local_10,1,4,1,param_1[1]);
  }
  if (local_e0 != (double *)0x0) {
    free_dvector(local_e0,1,param_1[1]);
  }
  if (local_e4 != (int *)0x0) {
    free_ivector(local_e4,1,param_1[1]);
  }
  return local_50[0];
}

//===== 0x1002b757 =====

undefined4 __cdecl
FUN_1002b757(int param_1,int param_2,int param_3,int param_4,int param_5,int param_6)

{
  undefined4 uVar1;
  double dVar2;
  uint local_30;
  int local_2c;
  int local_28;
  undefined8 local_24;
  int local_1c;
  int aiStack_18 [5];
  
  for (local_28 = 1; local_28 < 5; local_28 = local_28 + 1) {
    aiStack_18[local_28] = 0;
    *(undefined4 *)(param_5 + local_28 * 8) = 0;
    *(undefined4 *)(param_5 + 4 + local_28 * 8) = 0;
    *(undefined4 *)(param_6 + local_28 * 8) = 0;
    *(undefined4 *)(param_6 + 4 + local_28 * 8) = 0;
  }
  local_30 = 0;
  for (local_1c = 1; local_1c <= param_2; local_1c = local_1c + 1) {
    local_2c = 1;
    local_24 = (double)*(float *)(*(int *)(param_1 + 4) + local_1c * 4);
    for (local_28 = 2; local_28 < 5; local_28 = local_28 + 1) {
      if ((float)local_24 < *(float *)(*(int *)(param_1 + local_28 * 4) + local_1c * 4)) {
        local_2c = local_28;
        local_24 = (double)*(float *)(*(int *)(param_1 + local_28 * 4) + local_1c * 4);
      }
    }
    *(undefined4 *)(param_3 + local_1c * 8) = (undefined4)local_24;
    *(undefined4 *)(param_3 + 4 + local_1c * 8) = local_24._4_4_;
    *(int *)(param_4 + local_1c * 4) = local_2c;
    *(double *)(param_5 + local_2c * 8) = *(double *)(param_5 + local_2c * 8) + local_24;
    aiStack_18[local_2c] = aiStack_18[local_2c] + 1;
    local_30 = local_30 | 1 << ((char)local_2c - 1U & 0x1f);
  }
  if (local_30 == 0xf) {
    for (local_28 = 1; local_28 < 5; local_28 = local_28 + 1) {
      *(double *)(param_5 + local_28 * 8) =
           *(double *)(param_5 + local_28 * 8) / (double)aiStack_18[local_28];
    }
    for (local_28 = 1; local_28 <= param_2; local_28 = local_28 + 1) {
      dVar2 = *(double *)(param_3 + local_28 * 8) -
              *(double *)(param_5 + *(int *)(param_4 + local_28 * 4) * 8);
      *(double *)(param_6 + *(int *)(param_4 + local_28 * 4) * 8) =
           dVar2 * dVar2 + *(double *)(param_6 + *(int *)(param_4 + local_28 * 4) * 8);
    }
    for (local_28 = 1; local_28 < 5; local_28 = local_28 + 1) {
      dVar2 = sqrt(*(double *)(param_6 + local_28 * 8) / (double)aiStack_18[local_28]);
      *(double *)(param_6 + local_28 * 8) = dVar2;
    }
    uVar1 = 0;
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x1002b97b =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int __thiscall FUN_1002b97b(void *this,float *param_1)

{
  undefined4 uVar1;
  int iVar2;
  float *pfVar3;
  float *pfVar4;
  float local_f0;
  int local_e8;
  float local_e4 [7];
  int local_c8;
  int local_c4;
  uint local_c0;
  float **local_bc;
  int local_b8;
  int local_b4;
  float local_b0 [5];
  float local_9c [5];
  float local_88 [5];
  float local_74 [5];
  float **local_60;
  int local_5c;
  int local_58;
  float local_54 [5];
  float local_40 [5];
  float local_2c [5];
  float local_18 [5];
  
  local_58 = 1;
  local_bc = matrix(1,*(long *)((int)this + 4),1,4);
  local_60 = matrix(1,*(long *)((int)this + 4),1,4);
  if ((local_bc == (float **)0x0) || (local_60 == (float **)0x0)) {
    if (local_bc != (float **)0x0) {
      free_matrix(local_bc,1,*(long *)((int)this + 4),1,4);
    }
    if (local_60 != (float **)0x0) {
      free_matrix(local_60,1,*(long *)((int)this + 4),1,4);
    }
    *(undefined4 *)this = 1;
    return local_58;
  }
  pfVar3 = param_1;
  pfVar4 = local_54;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  pfVar3 = local_54;
  pfVar4 = local_b0;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  pfVar3 = param_1 + 5;
  pfVar4 = local_40;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  pfVar3 = local_40;
  pfVar4 = local_9c;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  pfVar3 = param_1 + 10;
  pfVar4 = local_2c;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  pfVar3 = local_2c;
  pfVar4 = local_88;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  pfVar3 = param_1 + 0xf;
  pfVar4 = local_18;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  pfVar3 = local_18;
  pfVar4 = local_74;
  for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
    *pfVar4 = *pfVar3;
    pfVar3 = pfVar3 + 1;
    pfVar4 = pfVar4 + 1;
  }
  local_b8 = 1;
  do {
    if ((local_58 != 1) || (2 < local_b8)) goto LAB_1002bf1c;
    local_58 = 0;
    for (local_5c = 0; local_5c < *(int *)((int)this + 4); local_5c = local_5c + 1) {
      FUN_1002c004((float *)(*(int *)((int)this + 8) + local_5c * 0x1c),(int)local_b0,(int)local_54,
                   (char *)(*(int *)((int)this + 8) + 0x1b + local_5c * 0x1c));
    }
    pfVar3 = local_54;
    pfVar4 = local_b0;
    for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
      *pfVar4 = *pfVar3;
      pfVar3 = pfVar3 + 1;
      pfVar4 = pfVar4 + 1;
    }
    pfVar3 = local_40;
    pfVar4 = local_9c;
    for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
      *pfVar4 = *pfVar3;
      pfVar3 = pfVar3 + 1;
      pfVar4 = pfVar4 + 1;
    }
    pfVar3 = local_2c;
    pfVar4 = local_88;
    for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
      *pfVar4 = *pfVar3;
      pfVar3 = pfVar3 + 1;
      pfVar4 = pfVar4 + 1;
    }
    pfVar3 = local_18;
    pfVar4 = local_74;
    for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
      *pfVar4 = *pfVar3;
      pfVar3 = pfVar3 + 1;
      pfVar4 = pfVar4 + 1;
    }
    local_c0 = 0;
    local_c4 = 0;
    *(undefined4 *)((int)this + 0x440) = 0;
    *(undefined4 *)((int)this + 0x43c) = 0;
    *(undefined4 *)((int)this + 0x438) = 0;
    *(undefined4 *)((int)this + 0x434) = 0;
    *(undefined4 *)((int)this + 0x430) = 0;
    for (local_5c = 1; local_5c <= *(int *)((int)this + 4); local_5c = local_5c + 1) {
      local_c8 = *(int *)((int)this + 8) + (local_5c + -1) * 0x1c;
      if (('\0' < *(char *)(local_c8 + 0x1b)) && (*(char *)(local_c8 + 0x1b) < '\x05')) {
        local_c4 = local_c4 + 1;
        *(int *)((int)this + *(char *)(local_c8 + 0x1b) * 4 + 0x430) =
             *(int *)((int)this + *(char *)(local_c8 + 0x1b) * 4 + 0x430) + 1;
        *(int *)((int)this + 0x430) = *(int *)((int)this + 0x430) + 1;
        for (local_b4 = 1; local_b4 < 5; local_b4 = local_b4 + 1) {
          local_bc[local_c4][local_b4] = *(float *)(local_c8 + -4 + local_b4 * 4);
          if (*(char *)(local_c8 + 0x1b) == local_b4) {
            local_f0 = local_bc[local_c4][local_b4];
          }
          else {
            local_f0 = 0.0;
          }
          local_60[local_c4][local_b4] = local_f0;
          local_c0 = local_c0 | 1 << (*(char *)(local_c8 + 0x1b) - 1U & 0x1f);
        }
      }
    }
    if (local_c0 == 0xf) {
      pfVar3 = local_b0;
      pfVar4 = (float *)((int)this + 0x3e0);
      for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
        *pfVar4 = *pfVar3;
        pfVar3 = pfVar3 + 1;
        pfVar4 = pfVar4 + 1;
      }
      pfVar3 = local_9c;
      pfVar4 = (float *)((int)this + 0x3f4);
      for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
        *pfVar4 = *pfVar3;
        pfVar3 = pfVar3 + 1;
        pfVar4 = pfVar4 + 1;
      }
      pfVar3 = local_88;
      pfVar4 = (float *)((int)this + 0x408);
      for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
        *pfVar4 = *pfVar3;
        pfVar3 = pfVar3 + 1;
        pfVar4 = pfVar4 + 1;
      }
      pfVar3 = local_74;
      pfVar4 = (float *)((int)this + 0x41c);
      for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
        *pfVar4 = *pfVar3;
        pfVar3 = pfVar3 + 1;
        pfVar4 = pfVar4 + 1;
      }
      for (local_5c = 0; local_5c < 4; local_5c = local_5c + 1) {
        for (local_b4 = 0; local_b4 < 4; local_b4 = local_b4 + 1) {
          local_e4[local_b4] = *(float *)((int)this + local_b4 * 4 + local_5c * 0x14 + 0x3e0);
        }
        FUN_100285dc(local_e4);
        uVar1 = ftol();
        *(undefined4 *)((int)this + local_5c * 4 + 0x444) = uVar1;
      }
      local_58 = FUN_1002c588(this,(int)local_bc,(int)local_60,local_c4);
      if (local_58 == 0) {
        local_58 = FUN_10027dd1((int)this + 0x390,0.6);
        if ((local_58 != 1) || (local_b8 != 2)) {
          *(undefined4 *)((int)this + 0x454) = 4;
          goto LAB_1002babf;
        }
      }
      *(undefined4 *)this = 7;
    }
    else {
      local_58 = 1;
      if (local_b8 != 1) {
        *(undefined4 *)this = 8;
LAB_1002bf1c:
        if (*(int *)this == 7) {
          local_e8 = 0;
          for (local_5c = 0; local_5c < 4; local_5c = local_5c + 1) {
            if (_DAT_10038e18 == local_b0[local_5c * 6]) {
              local_e8 = local_e8 + 1;
            }
          }
          if ((local_e8 == 4) && (iVar2 = FUN_10027c10((int)local_b0), iVar2 == 0)) {
            *(undefined4 *)this = 9;
            *(undefined4 *)((int)this + 0x454) = 5;
          }
        }
        free_matrix(local_bc,1,*(long *)((int)this + 4),1,4);
        free_matrix(local_60,1,*(long *)((int)this + 4),1,4);
        return local_58;
      }
    }
LAB_1002babf:
    local_b8 = local_b8 + 1;
  } while( true );
}

//===== 0x1002c004 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_1002c004(float *param_1,int param_2,int param_3,char *param_4)

{
  float *pfVar1;
  int iVar2;
  double dVar3;
  float local_58;
  float local_50;
  int local_4c;
  int local_48;
  float local_3c;
  int local_38;
  float local_34;
  int local_30;
  float afStack_2c [4];
  float local_1c;
  float local_18;
  float local_14;
  int local_10;
  float local_c;
  int local_8;
  
  local_14 = 1e+06;
  local_c = *param_1;
  for (local_8 = 1; local_8 < 4; local_8 = local_8 + 1) {
    if (local_c < param_1[local_8]) {
      local_c = param_1[local_8];
    }
  }
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    if (param_1[local_8] <= _DAT_10038e04) {
      local_58 = 0.0;
    }
    else {
      local_58 = param_1[local_8] / local_c;
    }
    afStack_2c[local_8] = local_58;
  }
  for (local_10 = 0; local_10 < 4; local_10 = local_10 + 1) {
    iVar2 = param_2 + local_10 * 0x14;
    local_50 = 0.0;
    for (local_8 = 0; (local_50 < local_14 && (local_8 < 4)); local_8 = local_8 + 1) {
      dVar3 = fabs((double)(afStack_2c[local_8] - *(float *)(iVar2 + local_8 * 4)));
      local_50 = (float)dVar3 + local_50;
    }
    if (local_50 < local_14) {
      local_14 = local_50;
      *param_4 = *(char *)(iVar2 + 0x10);
    }
  }
  pfVar1 = (float *)(param_3 + (*param_4 + -1) * 0x14);
  local_48 = -1;
  local_4c = -1;
  local_34 = 0.0;
  local_3c = 0.0;
  local_30 = 0;
  local_18 = *pfVar1;
  local_38 = 0;
  local_1c = afStack_2c[0];
  for (local_8 = 1; local_8 < 4; local_8 = local_8 + 1) {
    if (pfVar1[local_8] <= local_18) {
      if (local_34 < pfVar1[local_8]) {
        local_48 = local_8;
        local_34 = pfVar1[local_8];
      }
    }
    else {
      local_34 = local_18;
      local_48 = local_30;
      local_30 = local_8;
      local_18 = pfVar1[local_8];
    }
    if (afStack_2c[local_8] <= local_1c) {
      if (local_3c < afStack_2c[local_8]) {
        local_4c = local_8;
        local_3c = afStack_2c[local_8];
      }
    }
    else {
      local_3c = local_1c;
      local_4c = local_38;
      local_38 = local_8;
      local_1c = afStack_2c[local_8];
    }
  }
  if ((local_30 == local_38) && (local_48 == local_4c)) {
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      pfVar1[local_8] = ((4.0 - _DAT_10038e18) * pfVar1[local_8] + afStack_2c[local_8]) / 4.0;
    }
  }
  else {
    *param_4 = -1;
  }
  return;
}

//===== 0x1002c2cc =====

void __fastcall FUN_1002c2cc(int param_1)

{
  if (*(int *)(param_1 + 8) != 0) {
    operator_delete(*(void **)(param_1 + 8));
    *(undefined4 *)(param_1 + 8) = 0;
    *(undefined4 *)(param_1 + 4) = 0;
  }
  return;
}

//===== 0x1002c30b =====

void FUN_1002c30b(int param_1,undefined4 param_2,int param_3)

{
  float fVar1;
  float **ppfVar2;
  float **ppfVar3;
  int local_2c;
  int local_28;
  int local_18;
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037478;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  ppfVar2 = matrix(1,4,1,4);
  ppfVar3 = matrix(1,4,1,1);
  for (local_28 = 1; local_28 < 5; local_28 = local_28 + 1) {
    ppfVar3[local_28][1] = 1.0;
    for (local_18 = 1; local_18 < 5; local_18 = local_18 + 1) {
      fVar1 = 0.0;
      for (local_2c = 1; local_2c <= param_3; local_2c = local_2c + 1) {
        fVar1 = *(float *)(*(int *)(param_1 + local_2c * 4) + local_28 * 4) *
                *(float *)(*(int *)(param_1 + local_2c * 4) + local_18 * 4) + fVar1;
      }
      ppfVar2[local_28][local_18] = fVar1;
    }
  }
  local_8 = 0;
  FUN_100364a0((int)ppfVar2,4,(int)ppfVar3,1);
  FUN_1002c454();
  return;
}

//===== 0x1002c428 =====

undefined * Catch_1002c428(void)

{
  int unaff_EBP;
  
  **(undefined4 **)(unaff_EBP + -0x40) = 3;
  *(undefined4 *)(unaff_EBP + -0x2c) = 1;
  return FUN_1002c454;
}

//===== 0x1002c43e =====

undefined * Catch_1002c43e(void)

{
  int unaff_EBP;
  
  **(undefined4 **)(unaff_EBP + -0x40) = 4;
  *(undefined4 *)(unaff_EBP + -0x2c) = 1;
  return FUN_1002c454;
}

//===== 0x1002c454 =====

undefined4 FUN_1002c454(void)

{
  int unaff_EBP;
  
  *(undefined4 *)(unaff_EBP + -4) = 0xffffffff;
  if (*(int *)(unaff_EBP + -0x2c) == 0) {
    *(undefined4 *)(unaff_EBP + -0x14) = 1;
    while (*(int *)(unaff_EBP + -0x14) <= *(int *)(unaff_EBP + 0x10)) {
      *(undefined4 *)(unaff_EBP + -0x38) = 0;
      *(undefined4 *)(unaff_EBP + -0x34) = 0;
      *(undefined4 *)(unaff_EBP + -0x3c) = 0;
      *(undefined4 *)(unaff_EBP + -0x24) = 1;
      while (*(int *)(unaff_EBP + -0x24) < 5) {
        *(undefined4 *)(unaff_EBP + -0x1c) = 0;
        *(undefined4 *)(unaff_EBP + -0x18) = 0;
        *(undefined4 *)(unaff_EBP + -0x28) = 1;
        while (*(int *)(unaff_EBP + -0x28) < 5) {
          *(double *)(unaff_EBP + -0x1c) =
               (double)(*(float *)(*(int *)(*(int *)(unaff_EBP + -0x20) +
                                           *(int *)(unaff_EBP + -0x24) * 4) +
                                  *(int *)(unaff_EBP + -0x28) * 4) *
                        *(float *)(*(int *)(*(int *)(unaff_EBP + 8) +
                                           *(int *)(unaff_EBP + -0x14) * 4) +
                                  *(int *)(unaff_EBP + -0x28) * 4) +
                       (float)*(double *)(unaff_EBP + -0x1c));
          *(int *)(unaff_EBP + -0x28) = *(int *)(unaff_EBP + -0x28) + 1;
        }
        *(float *)(unaff_EBP + -0x48) = (float)*(double *)(unaff_EBP + -0x1c);
        *(float *)(*(int *)(*(int *)(unaff_EBP + 0xc) + *(int *)(unaff_EBP + -0x24) * 4) +
                  *(int *)(unaff_EBP + -0x14) * 4) = (float)*(double *)(unaff_EBP + -0x1c);
        if (*(double *)(unaff_EBP + -0x38) < *(double *)(unaff_EBP + -0x1c)) {
          *(undefined4 *)(unaff_EBP + -0x38) = *(undefined4 *)(unaff_EBP + -0x1c);
          *(undefined4 *)(unaff_EBP + -0x34) = *(undefined4 *)(unaff_EBP + -0x18);
          *(undefined4 *)(unaff_EBP + -0x3c) = *(undefined4 *)(unaff_EBP + -0x24);
        }
        *(int *)(unaff_EBP + -0x24) = *(int *)(unaff_EBP + -0x24) + 1;
      }
      *(int *)(unaff_EBP + -0x14) = *(int *)(unaff_EBP + -0x14) + 1;
    }
  }
  if (*(int *)(unaff_EBP + -0x30) != 0) {
    free_matrix(*(float ***)(unaff_EBP + -0x30),1,4,1,1);
  }
  if (*(int *)(unaff_EBP + -0x20) != 0) {
    free_matrix(*(float ***)(unaff_EBP + -0x20),1,4,1,4);
  }
  ExceptionList = *(void **)(unaff_EBP + -0xc);
  return *(undefined4 *)(unaff_EBP + -0x2c);
}

//===== 0x1002c588 =====

void __thiscall FUN_1002c588(void *this,int param_1,int param_2,int param_3)

{
  float fVar1;
  float fVar2;
  float **ppfVar3;
  float **ppfVar4;
  int local_38;
  int local_34;
  int local_20;
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037482;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  ppfVar3 = matrix(1,4,1,4);
  ppfVar4 = matrix(1,4,1,4);
  for (local_34 = 1; local_34 < 5; local_34 = local_34 + 1) {
    for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
      fVar2 = 0.0;
      fVar1 = 0.0;
      for (local_38 = 1; local_38 <= param_3; local_38 = local_38 + 1) {
        fVar1 = *(float *)(*(int *)(param_1 + local_38 * 4) + local_34 * 4) *
                *(float *)(*(int *)(param_1 + local_38 * 4) + local_20 * 4) + fVar1;
        fVar2 = *(float *)(*(int *)(param_1 + local_38 * 4) + local_34 * 4) *
                *(float *)(*(int *)(param_2 + local_38 * 4) + local_20 * 4) + fVar2;
      }
      ppfVar3[local_34][local_20] = fVar1;
      ppfVar4[local_34][local_20] = fVar2;
    }
  }
  local_8 = 0;
  FUN_100364a0((int)ppfVar3,4,(int)ppfVar4,4);
  for (local_34 = 1; local_34 < 5; local_34 = local_34 + 1) {
    for (local_20 = 1; local_20 < 5; local_20 = local_20 + 1) {
      *(float *)((int)this + local_20 * 4 + (local_34 + -1) * 0x10 + 0x38c) =
           ppfVar4[local_34][local_20];
    }
  }
  FUN_1002c76a();
  return;
}

//===== 0x1002c73e =====

undefined * Catch_1002c73e(void)

{
  int unaff_EBP;
  
  **(undefined4 **)(unaff_EBP + -0x3c) = 3;
  *(undefined4 *)(unaff_EBP + -0x38) = 1;
  return FUN_1002c76a;
}

//===== 0x1002c754 =====

undefined * Catch_1002c754(void)

{
  int unaff_EBP;
  
  **(undefined4 **)(unaff_EBP + -0x3c) = 4;
  *(undefined4 *)(unaff_EBP + -0x38) = 1;
  return FUN_1002c76a;
}

//===== 0x1002c76a =====

undefined4 FUN_1002c76a(void)

{
  int unaff_EBP;
  
  *(undefined4 *)(unaff_EBP + -4) = 0xffffffff;
  free_matrix(*(float ***)(unaff_EBP + -0x20),1,4,1,4);
  free_matrix(*(float ***)(unaff_EBP + -0x2c),1,4,1,4);
  ExceptionList = *(void **)(unaff_EBP + -0xc);
  return *(undefined4 *)(unaff_EBP + -0x38);
}

//===== 0x1002c7af =====

char * __fastcall FUN_1002c7af(int *param_1)

{
  int local_c;
  
  local_c = 0;
  while( true ) {
    if (9 < local_c) {
      return s_STS_UNKNOWN__10040b2c;
    }
    if (*(int *)(&DAT_10040a38 + local_c * 8) == *param_1) break;
    local_c = local_c + 1;
  }
  return (&PTR_s_STS_FAILURE_10040a3c)[local_c * 2];
}

//===== 0x1002c800 =====

undefined4 __thiscall FUN_1002c800(void *this,int param_1)

{
  return *(undefined4 *)(*(int *)((int)this + 0x20) + param_1 * 4);
}

//===== 0x1002c820 =====

/* public: __thiscall SW::SW(char const *,char const *) */

SW * __thiscall SW::SW(SW *this,char *param_1,char *param_2)

{
  size_t sVar1;
  void *pvVar2;
  int iVar3;
  int **ppiVar4;
  int iVar5;
  int local_10;
  int local_8;
  
                    /* 0x2c820  21  ??0SW@@QAE@PBD0@Z */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x1c) = 0x80000000;
  *(undefined4 *)(this + 0x20) = 0;
  *(undefined4 *)(this + 0x24) = 0;
  *(undefined4 *)(this + 0x28) = 0;
  *(undefined4 *)(this + 0x2c) = 0;
  *(undefined4 *)(this + 0x30) = 0;
  *(undefined4 *)(this + 0x34) = 0;
  *(undefined4 *)(this + 0x38) = 0;
  if ((param_1 != (char *)0x0) && (param_2 != (char *)0x0)) {
    sVar1 = strlen(param_1);
    *(size_t *)this = sVar1;
    sVar1 = strlen(param_2);
    *(size_t *)(this + 4) = sVar1;
    pvVar2 = operator_new(*(int *)this + 2);
    *(void **)(this + 0x14) = pvVar2;
    pvVar2 = operator_new(*(int *)(this + 4) + 2);
    *(void **)(this + 0x18) = pvVar2;
    if ((*(int *)(this + 0x14) == 0) || (*(int *)(this + 0x18) == 0)) {
      if (*(int *)(this + 0x14) != 0) {
        operator_delete(*(void **)(this + 0x14));
      }
      if (*(int *)(this + 0x18) != 0) {
        operator_delete(*(void **)(this + 0x18));
      }
      *(undefined4 *)(this + 0x18) = 0;
      *(undefined4 *)(this + 0x14) = 0;
    }
    else {
      strcpy((char *)(*(int *)(this + 0x14) + 1),param_1);
      strcpy((char *)(*(int *)(this + 0x18) + 1),param_2);
      iVar3 = *(int *)this + 1;
      iVar5 = *(int *)(this + 4) + 1;
      ppiVar4 = imatrix(1,iVar3,1,iVar5);
      *(int ***)(this + 0x28) = ppiVar4;
      ppiVar4 = imatrix(1,*(long *)this,1,*(long *)(this + 4));
      *(int ***)(this + 0x2c) = ppiVar4;
      if ((*(int *)(this + 0x28) == 0) || (*(int *)(this + 0x2c) == 0)) {
        operator_delete(*(void **)(this + 0x14));
        *(undefined4 *)(this + 0x14) = 0;
        operator_delete(*(void **)(this + 0x18));
        *(undefined4 *)(this + 0x18) = 0;
        if (*(int *)(this + 0x28) != 0) {
          free_imatrix(*(int ***)(this + 0x28),1,iVar3,1,iVar5);
        }
        *(undefined4 *)(this + 0x28) = 0;
        if (*(int *)(this + 0x2c) != 0) {
          free_imatrix(*(int ***)(this + 0x2c),1,*(long *)this,1,*(long *)(this + 4));
        }
        *(undefined4 *)(this + 0x2c) = 0;
      }
      else {
        sw_(this);
        for (local_8 = 2; local_8 <= iVar5; local_8 = local_8 + 1) {
          if (*(int *)(this + 0x1c) <
              *(int *)(*(int *)(*(int *)(this + 0x28) + iVar3 * 4) + local_8 * 4)) {
            *(undefined4 *)(this + 0x30) = *(undefined4 *)this;
            *(int *)(this + 0x34) = local_8 + -1;
            *(undefined4 *)(this + 0x1c) =
                 *(undefined4 *)(*(int *)(*(int *)(this + 0x28) + iVar3 * 4) + local_8 * 4);
          }
        }
        for (local_10 = 2; local_10 <= iVar3; local_10 = local_10 + 1) {
          if (*(int *)(this + 0x1c) <
              *(int *)(*(int *)(*(int *)(this + 0x28) + local_10 * 4) + iVar5 * 4)) {
            *(int *)(this + 0x30) = local_10 + -1;
            *(undefined4 *)(this + 0x34) = *(undefined4 *)(this + 4);
            *(undefined4 *)(this + 0x1c) =
                 *(undefined4 *)(*(int *)(*(int *)(this + 0x28) + local_10 * 4) + iVar5 * 4);
          }
        }
        swwalk_(this);
        concensus_(this);
      }
    }
  }
  return this;
}

//===== 0x1002cbaa =====

/* public: __thiscall SW::SW(class SW const &) */

SW * __thiscall SW::SW(SW *this,SW *param_1)

{
                    /* 0x2cbaa  20  ??0SW@@QAE@ABV0@@Z */
  *(undefined4 *)this = 0;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(undefined4 *)(this + 0xc) = 0;
  *(undefined4 *)(this + 0x10) = 0;
  *(undefined4 *)(this + 0x14) = 0;
  *(undefined4 *)(this + 0x18) = 0;
  *(undefined4 *)(this + 0x1c) = 0x80000000;
  *(undefined4 *)(this + 0x20) = 0;
  *(undefined4 *)(this + 0x24) = 0;
  *(undefined4 *)(this + 0x28) = 0;
  *(undefined4 *)(this + 0x2c) = 0;
  *(undefined4 *)(this + 0x30) = 0;
  *(undefined4 *)(this + 0x34) = 0;
  *(undefined4 *)(this + 0x38) = 0;
  operator=(this,param_1);
  return this;
}

//===== 0x1002cc5b =====

/* public: class SW const & __thiscall SW::operator=(class SW const &) */

SW * __thiscall SW::operator=(SW *this,SW *param_1)

{
  void *pvVar1;
  int **ppiVar2;
  int local_c;
  int local_8;
  
                    /* 0x2cc5b  53  ??4SW@@QAEABV0@ABV0@@Z */
  if (this != param_1) {
    if (*(int *)(this + 0x14) != 0) {
      operator_delete(*(void **)(this + 0x14));
      *(undefined4 *)(this + 0x14) = 0;
    }
    if (*(int *)(this + 0x18) != 0) {
      operator_delete(*(void **)(this + 0x18));
      *(undefined4 *)(this + 0x18) = 0;
    }
    if (*(int *)(this + 0x38) != 0) {
      operator_delete(*(void **)(this + 0x38));
      *(undefined4 *)(this + 0x38) = 0;
    }
    if (*(int *)(this + 0x20) != 0) {
      operator_delete(*(void **)(this + 0x20));
      *(undefined4 *)(this + 0x20) = 0;
    }
    if (*(int *)(this + 0x24) != 0) {
      operator_delete(*(void **)(this + 0x24));
      *(undefined4 *)(this + 0x24) = 0;
    }
    if (*(int *)(this + 0x28) != 0) {
      free_imatrix(*(int ***)(this + 0x28),1,*(int *)this + 1,1,*(int *)(this + 4) + 1);
      *(undefined4 *)(this + 0x28) = 0;
    }
    if (*(int *)(this + 0x2c) != 0) {
      free_imatrix(*(int ***)(this + 0x2c),1,*(long *)this,1,*(long *)(this + 4));
      *(undefined4 *)(this + 0x2c) = 0;
    }
    *(undefined4 *)this = *(undefined4 *)param_1;
    *(undefined4 *)(this + 4) = *(undefined4 *)(param_1 + 4);
    *(undefined4 *)(this + 8) = *(undefined4 *)(param_1 + 8);
    *(undefined4 *)(this + 0x1c) = *(undefined4 *)(param_1 + 0x1c);
    *(undefined4 *)(this + 0xc) = *(undefined4 *)(param_1 + 0xc);
    *(undefined4 *)(this + 0x10) = *(undefined4 *)(param_1 + 0x10);
    pvVar1 = operator_new(*(int *)this + 2);
    *(void **)(this + 0x14) = pvVar1;
    if (*(int *)(this + 0x14) != 0) {
      memcpy(*(void **)(this + 0x14),*(void **)(param_1 + 0x14),*(int *)this + 2);
    }
    pvVar1 = operator_new(*(int *)(this + 4) + 2);
    *(void **)(this + 0x18) = pvVar1;
    if (*(int *)(this + 0x18) != 0) {
      memcpy(*(void **)(this + 0x18),*(void **)(param_1 + 0x18),*(int *)(this + 4) + 2);
    }
    pvVar1 = operator_new(*(uint *)(this + 8));
    *(void **)(this + 0x20) = pvVar1;
    if (*(int *)(this + 0x20) != 0) {
      memcpy(*(void **)(this + 0x20),*(void **)(param_1 + 0x20),*(size_t *)(this + 8));
    }
    pvVar1 = operator_new(*(uint *)(this + 8));
    *(void **)(this + 0x24) = pvVar1;
    if (*(int *)(this + 0x24) != 0) {
      memcpy(*(void **)(this + 0x24),*(void **)(param_1 + 0x24),*(size_t *)(this + 8));
    }
    pvVar1 = operator_new(*(uint *)(this + 8));
    *(void **)(this + 0x38) = pvVar1;
    if (*(int *)(this + 0x38) != 0) {
      memcpy(*(void **)(this + 0x38),*(void **)(param_1 + 0x38),*(size_t *)(this + 8));
    }
    ppiVar2 = imatrix(1,*(int *)this + 1,1,*(int *)(this + 4) + 1);
    *(int ***)(this + 0x28) = ppiVar2;
    ppiVar2 = imatrix(1,*(long *)this,1,*(long *)(this + 4));
    *(int ***)(this + 0x2c) = ppiVar2;
    if ((*(int *)(this + 0x28) != 0) && (*(int *)(this + 0x2c) != 0)) {
      for (local_8 = 1; local_8 <= *(int *)this + 1; local_8 = local_8 + 1) {
        for (local_c = 1; local_c <= *(int *)(this + 4) + 1; local_c = local_c + 1) {
          *(undefined4 *)(*(int *)(*(int *)(this + 0x28) + local_8 * 4) + local_c * 4) =
               *(undefined4 *)(*(int *)(*(int *)(param_1 + 0x28) + local_8 * 4) + local_c * 4);
          if ((local_8 <= *(int *)this) && (local_c <= *(int *)(this + 4))) {
            *(undefined4 *)(*(int *)(*(int *)(this + 0x2c) + local_8 * 4) + local_c * 4) =
                 *(undefined4 *)(*(int *)(*(int *)(param_1 + 0x2c) + local_8 * 4) + local_c * 4);
          }
        }
      }
    }
  }
  return this;
}

//===== 0x1002d02b =====

/* public: __thiscall SW::~SW(void) */

void __thiscall SW::~SW(SW *this)

{
                    /* 0x2d02b  40  ??1SW@@QAE@XZ */
  if (*(int *)(this + 0x14) != 0) {
    operator_delete(*(void **)(this + 0x14));
    *(undefined4 *)(this + 0x14) = 0;
  }
  if (*(int *)(this + 0x18) != 0) {
    operator_delete(*(void **)(this + 0x18));
    *(undefined4 *)(this + 0x18) = 0;
  }
  if (*(int *)(this + 0x20) != 0) {
    operator_delete(*(void **)(this + 0x20));
    *(undefined4 *)(this + 0x20) = 0;
  }
  if (*(int *)(this + 0x24) != 0) {
    operator_delete(*(void **)(this + 0x24));
    *(undefined4 *)(this + 0x24) = 0;
  }
  if (*(int *)(this + 0x38) != 0) {
    operator_delete(*(void **)(this + 0x38));
    *(undefined4 *)(this + 0x38) = 0;
  }
  if (*(int *)(this + 0x28) != 0) {
    free_imatrix(*(int ***)(this + 0x28),1,*(int *)this + 1,1,*(int *)(this + 4) + 1);
    *(undefined4 *)(this + 0x28) = 0;
  }
  if (*(int *)(this + 0x2c) != 0) {
    free_imatrix(*(int ***)(this + 0x2c),1,*(long *)this,1,*(long *)(this + 4));
    *(undefined4 *)(this + 0x2c) = 0;
  }
  return;
}

//===== 0x1002d16c =====

/* WARNING: Restarted to delay deadcode elimination for space: stack */
/* private: void __thiscall SW::sw_(void)const  */

void __thiscall SW::sw_(SW *this)

{
  int local_30;
  int local_2c;
  int local_28;
  int aiStack_24 [4];
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x2d16c  422  ?sw_@SW@@ABEXXZ */
  for (local_c = 1; local_c <= *(int *)this + 1; local_c = local_c + 1) {
    for (local_8 = 1; local_8 <= *(int *)(this + 4) + 1; local_8 = local_8 + 1) {
      *(undefined4 *)(*(int *)(*(int *)(this + 0x28) + local_c * 4) + local_8 * 4) = 0;
      if ((local_c <= *(int *)this) && (local_8 <= *(int *)(this + 4))) {
        *(undefined4 *)(*(int *)(*(int *)(this + 0x2c) + local_c * 4) + local_8 * 4) = 0;
      }
    }
  }
  for (local_10 = 1; local_10 <= *(int *)this; local_10 = local_10 + 1) {
    for (local_14 = 1; local_14 <= *(int *)(this + 4); local_14 = local_14 + 1) {
      local_28 = *(int *)(*(int *)(*(int *)(this + 0x28) + local_10 * 4) + 4 + local_14 * 4) + -3;
      aiStack_24[1] = local_28;
      aiStack_24[2] =
           *(int *)(*(int *)(*(int *)(this + 0x28) + local_10 * 4) + local_14 * 4) +
           (-(uint)(*(char *)(*(int *)(this + 0x14) + local_10) !=
                   *(char *)(*(int *)(this + 0x18) + local_14)) & 0xfffffffe) + 1;
      aiStack_24[3] =
           *(int *)(*(int *)(*(int *)(this + 0x28) + 4 + local_10 * 4) + local_14 * 4) + -3;
      local_2c = 1;
      for (local_30 = 2; local_30 < 4; local_30 = local_30 + 1) {
        if (local_28 < aiStack_24[local_30]) {
          local_2c = local_30;
          local_28 = aiStack_24[local_30];
        }
      }
      *(int *)(*(int *)(*(int *)(this + 0x28) + 4 + local_10 * 4) + 4 + local_14 * 4) = local_28;
      *(int *)(*(int *)(*(int *)(this + 0x2c) + local_10 * 4) + local_14 * 4) = local_2c + -2;
    }
  }
  return;
}

//===== 0x1002d331 =====

/* private: void __thiscall SW::swwalk_(void) */

void __thiscall SW::swwalk_(SW *this)

{
  int iVar1;
  char cVar2;
  void *pvVar3;
  void *pvVar4;
  void *pvVar5;
  int iVar6;
  int local_1c;
  int local_18;
  int local_c;
  int local_8;
  
                    /* 0x2d331  423  ?swwalk_@SW@@AAEXXZ */
  iVar6 = *(int *)(this + 0x30) + *(int *)(this + 0x34);
  pvVar3 = operator_new(iVar6 + 2);
  if (pvVar3 != (void *)0x0) {
    pvVar4 = operator_new(iVar6 + 2);
    if (pvVar4 == (void *)0x0) {
      operator_delete(pvVar3);
    }
    else {
      local_18 = *(int *)(this + 0x30);
      local_c = *(int *)(this + 0x34);
      for (local_8 = 0; local_1c = iVar6, local_8 <= iVar6 + 1; local_8 = local_8 + 1) {
        *(undefined1 *)((int)pvVar4 + local_8) = 0;
        *(undefined1 *)((int)pvVar3 + local_8) = 0;
      }
      while ((0 < local_18 && (0 < local_c))) {
        iVar1 = *(int *)(*(int *)(*(int *)(this + 0x2c) + local_18 * 4) + local_c * 4);
        if (iVar1 == -1) {
          *(undefined1 *)((int)pvVar3 + local_1c) =
               *(undefined1 *)(*(int *)(this + 0x14) + local_18);
          local_18 = local_18 + -1;
          cVar2 = gapchar(this);
          *(char *)((int)pvVar4 + local_1c) = cVar2;
        }
        else if (iVar1 == 0) {
          *(undefined1 *)((int)pvVar3 + local_1c) =
               *(undefined1 *)(*(int *)(this + 0x14) + local_18);
          local_18 = local_18 + -1;
          *(undefined1 *)((int)pvVar4 + local_1c) = *(undefined1 *)(*(int *)(this + 0x18) + local_c)
          ;
          local_c = local_c + -1;
        }
        else {
          if (iVar1 != 1) {
            fprintf((FILE *)(_iob_exref + 0x40),s_SW__swwalk____encountered__d__no_10040b60,
                    *(undefined4 *)(*(int *)(*(int *)(this + 0x2c) + local_18 * 4) + local_c * 4));
            operator_delete(pvVar3);
            operator_delete(pvVar4);
            return;
          }
          cVar2 = gapchar(this);
          *(char *)((int)pvVar3 + local_1c) = cVar2;
          *(undefined1 *)((int)pvVar4 + local_1c) = *(undefined1 *)(*(int *)(this + 0x18) + local_c)
          ;
          local_c = local_c + -1;
        }
        local_1c = local_1c + -1;
      }
      local_1c = local_1c + 1;
      *(int *)(this + 0xc) = local_18;
      *(int *)(this + 0x10) = local_c;
      if (*(int *)(this + 0x20) != 0) {
        operator_delete(*(void **)(this + 0x20));
        *(undefined4 *)(this + 0x20) = 0;
      }
      if (*(int *)(this + 0x24) != 0) {
        operator_delete(*(void **)(this + 0x24));
        *(undefined4 *)(this + 0x24) = 0;
      }
      *(int *)(this + 8) = (iVar6 - local_1c) + 2;
      pvVar5 = operator_new(*(uint *)(this + 8));
      *(void **)(this + 0x20) = pvVar5;
      pvVar5 = operator_new(*(uint *)(this + 8));
      *(void **)(this + 0x24) = pvVar5;
      if (*(int *)(this + 0x20) != 0) {
        strcpy(*(char **)(this + 0x20),(char *)((int)pvVar3 + local_1c));
      }
      if (*(int *)(this + 0x24) != 0) {
        strcpy(*(char **)(this + 0x24),(char *)((int)pvVar4 + local_1c));
      }
      operator_delete(pvVar3);
      operator_delete(pvVar4);
    }
  }
  return;
}

//===== 0x1002d629 =====

/* public: void __thiscall SW::debug(void)const  */

void __thiscall SW::debug(SW *this)

{
  undefined *puVar1;
  undefined *local_24;
  undefined *local_20;
  undefined *local_1c;
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x2d629  131  ?debug@SW@@QBEXXZ */
  printf(s_SW____p_10040b90,this);
  printf(s_vsz_____2d_hsz___2d_outsz___2d_10040b9c,*(undefined4 *)this,*(undefined4 *)(this + 4),
         *(undefined4 *)(this + 8));
  if (*(int *)(this + 0x14) == 0) {
    local_1c = &DAT_10040bc0;
  }
  else {
    local_1c = (undefined *)(*(int *)(this + 0x14) + 1);
  }
  printf(s_vseq______s__10040bc8,local_1c);
  if (*(int *)(this + 0x18) == 0) {
    local_20 = &DAT_10040bd8;
  }
  else {
    local_20 = (undefined *)(*(int *)(this + 0x18) + 1);
  }
  printf(s_hseq______s__10040be0,local_20);
  printf(s_vpos0_____2d_hpos0_____2d_10040bf0,*(undefined4 *)(this + 0xc),
         *(undefined4 *)(this + 0x10));
  printf(s_score___2d_10040c10,*(undefined4 *)(this + 0x1c));
  printf(s_vcoord_____4d_hcoord_____4d_10040c20,*(undefined4 *)(this + 0x30),
         *(undefined4 *)(this + 0x34));
  if (*(int *)(this + 0x20) == 0) {
    local_24 = &DAT_10040c40;
  }
  else {
    local_24 = *(undefined **)(this + 0x20);
  }
  printf(s_vseqout______s__10040c48,local_24);
  if (*(int *)(this + 0x24) == 0) {
    puVar1 = &DAT_10040c5c;
  }
  else {
    puVar1 = *(undefined **)(this + 0x24);
  }
  printf(s_hseqout______s__10040c64,puVar1);
  printf(s_scores___10040c78);
  if (*(int *)(this + 0x28) != 0) {
    for (local_8 = 1; local_8 <= *(int *)this + 1; local_8 = local_8 + 1) {
      printf(&DAT_10040c84,puVar1);
      for (local_c = 1; local_c <= *(int *)(this + 4) + 1; local_c = local_c + 1) {
        printf(&DAT_10040c88,
               *(undefined4 *)(*(int *)(*(int *)(this + 0x28) + local_8 * 4) + local_c * 4));
      }
      printf(&DAT_10040c90);
    }
  }
  printf(s_path___10040c94,puVar1);
  if (*(int *)(this + 0x2c) != 0) {
    for (local_10 = 1; local_10 <= *(int *)this; local_10 = local_10 + 1) {
      printf(&DAT_10040c9c);
      for (local_14 = 1; local_14 <= *(int *)(this + 4); local_14 = local_14 + 1) {
        printf(&DAT_10040ca0,
               *(undefined4 *)(*(int *)(*(int *)(this + 0x2c) + local_10 * 4) + local_14 * 4));
      }
      printf(&DAT_10040ca8);
    }
  }
  return;
}

//===== 0x1002d89d =====

/* public: int __thiscall SW::showAlignment(struct _iobuf *,char const *)const  */

int __thiscall SW::showAlignment(SW *this,_iobuf *param_1,char *param_2)

{
  char *_Str;
  char *_Str_00;
  char *pcVar1;
  int iVar2;
  size_t sVar3;
  int iVar4;
  size_t local_34;
  size_t local_30;
  int local_24;
  int local_20;
  size_t local_14;
  
                    /* 0x2d89d  397  ?showAlignment@SW@@QBEHPAU_iobuf@@PBD@Z */
  _Str = vout(this);
  _Str_00 = hout(this);
  pcVar1 = concensus(this);
  local_20 = 0;
  if ((_Str == (char *)0x0) || (_Str_00 == (char *)0x0)) {
    iVar2 = 0;
  }
  else {
    sVar3 = strlen(_Str);
    local_30 = strlen(_Str_00);
    if ((int)sVar3 < (int)local_30) {
      local_30 = sVar3;
    }
    local_14 = local_30;
    if (param_2 != (char *)0x0) {
      fprintf(param_1,&DAT_10040cac,param_2);
    }
    if (param_1 == (_iobuf *)0x0) {
      param_1 = (_iobuf *)(_iob_exref + 0x20);
    }
    iVar2 = Annotate::getNumFwhmGapLen((Annotate *)this);
    iVar4 = SSNODE::SWold((SSNODE *)this);
    fprintf(param_1,s_Alignment_begins_at__d_in_S1_and_10040cb0,iVar4,iVar2);
    for (; 0 < (int)local_14; local_14 = local_14 - local_34) {
      if ((int)local_14 < 0x33) {
        local_34 = local_14;
      }
      else {
        local_34 = 0x32;
      }
      fprintf(param_1,&DAT_10040cdc);
      for (local_24 = 1; local_24 <= (int)local_34; local_24 = local_24 + 1) {
        fprintf(param_1,&DAT_10040ce4,(int)_Str[local_20 + local_24 + -1]);
        if (local_24 % 10 == 0) {
          fprintf(param_1,&DAT_10040ce8);
        }
      }
      fprintf(param_1,&DAT_10040cec);
      fprintf(param_1,&DAT_10040cf0);
      for (local_24 = 1; local_24 <= (int)local_34; local_24 = local_24 + 1) {
        fprintf(param_1,&DAT_10040cf8,(int)_Str_00[local_20 + local_24 + -1]);
        if (local_24 % 10 == 0) {
          fprintf(param_1,&DAT_10040cfc);
        }
      }
      fprintf(param_1,&DAT_10040d00);
      fprintf(param_1,&DAT_10040d04);
      for (local_24 = 1; local_24 <= (int)local_34; local_24 = local_24 + 1) {
        fprintf(param_1,&DAT_10040d0c,(int)pcVar1[local_20 + local_24 + -1]);
        if (local_24 % 10 == 0) {
          fprintf(param_1,&DAT_10040d10);
        }
      }
      fprintf(param_1,&DAT_10040d14);
      local_20 = local_20 + local_34;
    }
    iVar2 = 1;
  }
  return iVar2;
}

//===== 0x1002db3a =====

/* private: void __thiscall SW::concensus_(void) */

void __thiscall SW::concensus_(SW *this)

{
  char cVar1;
  void *pvVar2;
  char *local_10;
  int local_c;
  char *local_8;
  
                    /* 0x2db3a  116  ?concensus_@SW@@AAEXXZ */
  if (*(int *)(this + 0x20) != 0) {
    pvVar2 = operator_new(*(int *)(this + 8) + 1);
    *(void **)(this + 0x38) = pvVar2;
    local_8 = *(char **)(this + 0x20);
    local_10 = *(char **)(this + 0x24);
    for (local_c = 0; local_c < *(int *)(this + 8); local_c = local_c + 1) {
      if (*local_8 == *local_10) {
LAB_1002dbce:
        *(char *)(*(int *)(this + 0x38) + local_c) = *local_8;
      }
      else {
        cVar1 = gapchar(this);
        if (cVar1 == *local_8) goto LAB_1002dbce;
        cVar1 = gapchar(this);
        if (cVar1 == *local_10) {
          *(char *)(*(int *)(this + 0x38) + local_c) = *local_10;
        }
        else {
          cVar1 = gapchar(this);
          *(char *)(*(int *)(this + 0x38) + local_c) = cVar1;
        }
      }
      local_8 = local_8 + 1;
      local_10 = local_10 + 1;
    }
    *(undefined1 *)(*(int *)(this + 0x38) + local_c) = 0;
  }
  return;
}

//===== 0x1002dc40 =====

/* public: __thiscall Wvfm::Wvfm(void) */

Wvfm * __thiscall Wvfm::Wvfm(Wvfm *this)

{
  undefined4 local_20;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x2dc40  28  ??0Wvfm@@QAE@XZ */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003749c;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  Annotate::Annotate((Annotate *)(this + 4));
  local_8 = 0;
  *(undefined4 *)(this + 0xb0) = 0;
  *(undefined4 *)(this + 0xb4) = 0;
  *(undefined4 *)(this + 0xb8) = 0;
  *(undefined4 *)(this + 0xbc) = 0;
  *(undefined4 *)(this + 0xc0) = 0;
  *(undefined4 *)(this + 0xc4) = 0;
  *(undefined4 *)(this + 200) = 0;
  *(undefined4 *)(this + 0xcc) = 0;
  *(undefined4 *)(this + 0xd0) = 0;
  *(undefined4 *)(this + 0xd4) = 0;
  *(undefined4 *)(this + 0xd8) = 0;
  *(undefined4 *)(this + 0x168) = 0;
  *(undefined4 *)(this + 0x16c) = 1;
  this[0x170] = (Wvfm)0x1;
  *(undefined4 *)(this + 0x174) = 0;
  *(undefined4 *)(this + 0x178) = 0;
  *(undefined4 *)(this + 0x1b0) = 0;
  *(undefined4 *)(this + 0x1b4) = 0;
  *(undefined4 *)(this + 0x1b8) = 0;
  *(undefined4 *)(this + 0x1bc) = 0;
  ObsInpSpec::ObsInpSpec((ObsInpSpec *)(this + 0x210));
  *(undefined4 *)(this + 0x2f8) = 0;
  *(undefined4 *)(this + 0x2fc) = 0;
  *(undefined4 *)(this + 0x300) = 0;
  memset(this + 0xdc,0,6);
  for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
    this[local_14 * 0x14 + 0x1d0] = (Wvfm)0x0;
    for (local_18 = 0; local_18 < 4; local_18 = local_18 + 1) {
      if (local_14 == local_18) {
        local_20 = 0x3ff00000;
      }
      else {
        local_20 = 0;
      }
      *(undefined4 *)(this + local_18 * 8 + local_14 * 0x20 + 0xe8) = 0;
      *(undefined4 *)(this + local_18 * 8 + local_14 * 0x20 + 0xec) = local_20;
      *(undefined4 *)(this + local_18 * 4 + local_14 * 0x14 + 0x1c0) = 0;
    }
  }
  *(undefined4 *)(this + 0x168) = 3;
  *(undefined4 *)(this + 0x17c) = 0;
  for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
    for (local_18 = 0; local_18 < 3; local_18 = local_18 + 1) {
      *(undefined4 *)(this + local_18 * 4 + local_14 * 0xc + 0x180) = 0;
    }
  }
  ExceptionList = local_10;
  return this;
}

//===== 0x1002def0 =====

/* public: int __thiscall Wvfm::dim(int) */

int __thiscall Wvfm::dim(Wvfm *this,int param_1)

{
  double **ppdVar1;
  float *pfVar2;
  int local_10;
  int local_8;
  
                    /* 0x2def0  138  ?dim@Wvfm@@QAEHH@Z */
  if (*(int *)(this + 0xc4) != 0) {
    free_dmatrix(*(double ***)(this + 0xc4),1,*(long *)(this + 0xb0),1,*(long *)(this + 0xb4));
  }
  if (*(int *)(this + 0x300) != 0) {
    free_vector(*(float **)(this + 0x300),1,*(long *)(this + 0xb0));
  }
  *(undefined4 *)(this + 0xb4) = 4;
  *(int *)(this + 0xb0) = param_1;
  ppdVar1 = dmatrix(1,param_1,1,4);
  *(double ***)(this + 0xc4) = ppdVar1;
  pfVar2 = vector(1,*(long *)(this + 0xb0));
  *(float **)(this + 0x300) = pfVar2;
  for (local_8 = 1; local_8 <= *(int *)(this + 0xb0); local_8 = local_8 + 1) {
    *(undefined4 *)(*(int *)(this + 0x300) + local_8 * 4) = 0;
  }
  *(undefined4 *)(this + 0xb8) = 1;
  *(undefined4 *)(this + 0xbc) = *(undefined4 *)(this + 0xb0);
  *(undefined4 *)(this + 0x168) = 1;
  if ((*(int *)(this + 0xc4) == 0) || (*(int *)(this + 0x300) == 0)) {
    local_10 = 0;
  }
  else {
    local_10 = 1;
  }
  return local_10;
}

//===== 0x1002e03c =====

/* public: __thiscall Wvfm::Wvfm(char const *,char const *,char const *,enum Wvfm::DATASRC,enum
   Wvfm::Method) */

Wvfm * __thiscall
Wvfm::Wvfm(Wvfm *this,char *param_1,char *param_2,char *param_3,DATASRC param_4,Method param_5)

{
  int iVar1;
  size_t sVar2;
  char *pcVar3;
  undefined4 local_170;
  undefined1 local_168 [4];
  undefined1 local_164 [4];
  undefined1 local_160 [8];
  int *local_158;
  int local_154;
  uint local_150;
  uint local_14c;
  int local_148;
  int local_144;
  FILE *local_140;
  int **local_13c;
  int local_138;
  int local_134;
  int local_130 [2];
  long local_128;
  char local_124 [64];
  char local_e4 [64];
  int local_a4;
  int local_a0;
  float local_9c;
  int local_98;
  int local_94;
  char local_90 [128];
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x2e03c  27  ??0Wvfm@@QAE@PBD00W4DATASRC@0@W4Method@0@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_100374c7;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  Annotate::Annotate((Annotate *)(this + 4));
  local_8 = 0;
  *(undefined4 *)(this + 0xb0) = 0;
  *(undefined4 *)(this + 0xb4) = 0;
  *(undefined4 *)(this + 0xb8) = 1;
  *(undefined4 *)(this + 0xbc) = 0;
  *(DATASRC *)(this + 0xc0) = param_4;
  *(undefined4 *)(this + 0xc4) = 0;
  *(undefined4 *)(this + 200) = 0;
  *(undefined4 *)(this + 0xcc) = 0;
  *(undefined4 *)(this + 0xd0) = 0;
  *(undefined4 *)(this + 0xd4) = 0;
  *(Method *)(this + 0xd8) = param_5;
  *(undefined4 *)(this + 0x168) = 0;
  *(undefined4 *)(this + 0x16c) = 1;
  this[0x170] = (Wvfm)0x1;
  *(undefined4 *)(this + 0x174) = 0;
  *(undefined4 *)(this + 0x178) = 0;
  *(undefined4 *)(this + 0x1b0) = 0;
  *(undefined4 *)(this + 0x1b4) = 0;
  *(undefined4 *)(this + 0x1b8) = 0;
  *(undefined4 *)(this + 0x1bc) = 0;
  ObsInpSpec::ObsInpSpec((ObsInpSpec *)(this + 0x210));
  local_8 = CONCAT31(local_8._1_3_,1);
  *(undefined4 *)(this + 0x2f8) = 0;
  *(undefined4 *)(this + 0x2fc) = 0;
  *(undefined4 *)(this + 0x300) = 0;
  local_140 = (FILE *)0x0;
  iVar1 = licenseOk(this);
  if (iVar1 != 0) {
    memset(this + 0xdc,0,6);
    this[0xe0] = (Wvfm)0x2d;
    for (local_94 = 0; local_94 < 4; local_94 = local_94 + 1) {
      this[local_94 * 0x14 + 0x1d0] = (Wvfm)0x0;
      for (local_a0 = 0; local_a0 < 4; local_a0 = local_a0 + 1) {
        if (local_94 == local_a0) {
          local_170 = 0x3ff00000;
        }
        else {
          local_170 = 0;
        }
        *(undefined4 *)(this + local_a0 * 8 + local_94 * 0x20 + 0xe8) = 0;
        *(undefined4 *)(this + local_a0 * 8 + local_94 * 0x20 + 0xec) = local_170;
        *(undefined4 *)(this + local_a0 * 4 + local_94 * 0x14 + 0x1c0) = 0;
      }
    }
    *(undefined4 *)(this + 0x17c) = 0;
    for (local_94 = 0; local_94 < 4; local_94 = local_94 + 1) {
      for (local_a0 = 0; local_a0 < 3; local_a0 = local_a0 + 1) {
        *(undefined4 *)(this + local_a0 * 4 + local_94 * 0xc + 0x180) = 0;
      }
    }
    if (param_2 == (char *)0x0) {
      if (param_3 != (char *)0x0) {
        local_14c = 0;
        while (sVar2 = strlen(param_3), local_14c < sVar2) {
          iVar1 = toupper((int)param_3[local_14c]);
          this[local_14c + 0xdc] = SUB41(iVar1,0);
          local_14c = local_14c + 1;
        }
        this[0xe0] = (Wvfm)0x2d;
        this[0xe1] = (Wvfm)0x0;
      }
    }
    else {
      local_140 = fopen(param_2,&DAT_10040d64);
      if (local_140 == (FILE *)0x0) {
        *(undefined4 *)(this + 0x168) = 4;
        ExceptionList = local_10;
        return this;
      }
      if (param_3 == (char *)0x0) {
        fscanf(local_140,&DAT_10040d68);
        fscanf(local_140,&DAT_10040d6c);
        fscanf(local_140,&DAT_10040d70);
      }
      else {
        local_150 = 0;
        while (sVar2 = strlen(param_3), local_150 < sVar2) {
          iVar1 = toupper((int)param_3[local_150]);
          this[local_150 + 0xdc] = SUB41(iVar1,0);
          local_150 = local_150 + 1;
        }
      }
      this[0xe0] = (Wvfm)0x2d;
      this[0xe1] = (Wvfm)0x0;
      for (local_94 = 0; local_94 < 4; local_94 = local_94 + 1) {
        iVar1 = fscanf(local_140,s__lf__lf__lf__lf_10040d74,this + local_94 * 0x20 + 0xe8,
                       this + local_94 * 0x20 + 0xf0,this + local_94 * 0x20 + 0xf8);
        if (iVar1 != 4) {
          fprintf((FILE *)(_iob_exref + 0x40),s_SSM_file__s__has___s__instead_of_10040d84,param_2);
          fprintf((FILE *)(_iob_exref + 0x40),s_Wrong_file__or_incorrect_file_fo_10040db4);
                    /* WARNING: Subroutine does not return */
          exit(1);
        }
      }
      fclose(local_140);
      this[0x170] = (Wvfm)0x0;
    }
    if ((param_1 == (char *)0x0) ||
       (local_140 = fopen(param_1,&DAT_10040ddc), local_140 == (FILE *)0x0)) {
      *(undefined4 *)(this + 0x168) = 5;
    }
    else {
      local_a4 = fscanf(local_140,s__s__s__d__d__f__d_10040de0,local_124,local_e4,local_130,
                        &local_128,&local_9c);
      if (local_130[0] == 4) {
        if ((*(int *)(this + 0xc0) == 5) && (iVar1 = strncmp(local_124,&DAT_10040e44,4), iVar1 != 0)
           ) {
          fprintf((FILE *)(_iob_exref + 0x40),s_Header_field_1_contains___s__not_10040e54,local_124,
                  &DAT_10040e4c);
          *(undefined4 *)(this + 0x168) = 9;
        }
        else {
          if (local_9c == 1.75) {
            *(undefined4 *)(this + 0x16c) = 1;
          }
          else {
            if (local_9c != 3.5) {
              fprintf((FILE *)(_iob_exref + 0x40),s__s__d___4___4_2f__neither_1_75__n_10040eb4,
                      s_C__Program_Files_DevStudio_MyPro_10040e7c,0xc0,(double)local_9c);
              *(undefined4 *)(this + 0x168) = 9;
              ExceptionList = local_10;
              return this;
            }
            *(undefined4 *)(this + 0x16c) = 2;
          }
          local_98 = 1;
          for (local_138 = 0; local_138 < 4; local_138 = local_138 + 1) {
            for (local_154 = 0; local_154 < 4; local_154 = local_154 + 1) {
              if (local_e4[local_138] == (&DAT_10038e48)[local_154]) {
                local_98 = local_98 * (char)(&DAT_10038e50)[local_154];
                break;
              }
            }
          }
          if (local_98 == 0x483) {
            strncpy((char *)(this + 0xdc),local_e4,4);
            this[0xe0] = (Wvfm)0x2d;
            this[0xe1] = (Wvfm)0x0;
          }
          if (this[0xdc] == (Wvfm)0x0) {
            *(undefined4 *)(this + 0x168) = 8;
          }
          else {
            local_13c = imatrix(1,local_128,1,4);
            if (local_13c == (int **)0x0) {
              *(undefined4 *)(this + 0x168) = 2;
            }
            else {
              local_144 = 1;
              while (((local_144 <= local_128 &&
                      (pcVar3 = fgets(local_90,0x80,local_140), pcVar3 != (char *)0x0)) &&
                     (iVar1 = strncmp(local_90,s_INTENSITY_DATA_END__10040ee0,0x13), iVar1 != 0))) {
                local_158 = local_13c[local_144];
                iVar1 = sscanf(local_90,s__f__f__f__f_10040ef4,local_168,local_164,local_160);
                if (iVar1 != 4) {
                  free_imatrix(local_13c,1,local_128,1,4);
                  *(undefined4 *)(this + 0x168) = 6;
                  ExceptionList = local_10;
                  return this;
                }
                iVar1 = ftol();
                local_158[1] = iVar1;
                iVar1 = ftol();
                local_158[2] = iVar1;
                iVar1 = ftol();
                local_158[3] = iVar1;
                iVar1 = ftol();
                local_158[4] = iVar1;
                local_144 = local_144 + 1;
              }
              fclose(local_140);
              local_144 = local_144 + -1;
              iVar1 = dim(this,local_144);
              if (iVar1 == 0) {
                free_imatrix(local_13c,1,local_128,1,4);
                *(undefined4 *)(this + 0x168) = 2;
              }
              else {
                for (local_134 = 1; local_134 <= *(int *)(this + 0xb0); local_134 = local_134 + 1) {
                  *(undefined4 *)(*(int *)(this + 0x300) + local_134 * 4) = 0;
                  for (local_148 = 1; local_148 <= *(int *)(this + 0xb4); local_148 = local_148 + 1)
                  {
                    *(double *)(*(int *)(*(int *)(this + 0xc4) + local_134 * 4) + local_148 * 8) =
                         (double)local_13c[local_134][local_148];
                  }
                }
                free_imatrix(local_13c,1,local_128,1,4);
                *(undefined4 *)(this + 0x168) = 1;
              }
            }
          }
        }
      }
      else {
        fprintf((FILE *)(_iob_exref + 0x40),s__s__d___3___d__not_4_10040e2c,
                s_C__Program_Files_DevStudio_MyPro_10040df4,0xb2,local_130[0]);
        *(undefined4 *)(this + 0x168) = 9;
      }
    }
  }
  ExceptionList = local_10;
  return this;
}

//===== 0x1002ebf6 =====

/* public: int __thiscall Wvfm::licenseOk(void) */

int __thiscall Wvfm::licenseOk(Wvfm *this)

{
  int iVar1;
  tm *ptVar2;
  time_t tVar3;
  undefined4 local_24 [2];
  undefined4 local_1c [2];
  undefined4 local_14 [2];
  undefined4 local_c [2];
  
                    /* 0x2ebf6  262  ?licenseOk@Wvfm@@QAEHXZ */
  if (*(int *)(this + 0xc0) == 2) {
    iVar1 = 1;
  }
  else if (*(int *)(this + 0xc0) == 4) {
    tVar3 = time((time_t *)0x0);
    local_c[0] = (undefined4)tVar3;
    ptVar2 = localtime((time_t *)local_c);
    if (ptVar2->tm_year < 0x66) {
      if ((ptVar2->tm_year == 0x65) && (8 < ptVar2->tm_mon)) {
        *(undefined4 *)(this + 0x168) = 0x14;
        iVar1 = 0;
      }
      else {
        iVar1 = 1;
      }
    }
    else {
      *(undefined4 *)(this + 0x168) = 0x14;
      iVar1 = 0;
    }
  }
  else if (*(int *)(this + 0xc0) == 5) {
    tVar3 = time((time_t *)0x0);
    local_14[0] = (undefined4)tVar3;
    ptVar2 = localtime((time_t *)local_14);
    if (ptVar2->tm_year < 0x65) {
      if ((ptVar2->tm_year == 100) && (6 < ptVar2->tm_mon)) {
        *(undefined4 *)(this + 0x168) = 0x14;
        iVar1 = 0;
      }
      else {
        iVar1 = 1;
      }
    }
    else {
      *(undefined4 *)(this + 0x168) = 0x14;
      iVar1 = 0;
    }
  }
  else if (*(int *)(this + 0xc0) == 6) {
    tVar3 = time((time_t *)0x0);
    local_1c[0] = (undefined4)tVar3;
    ptVar2 = localtime((time_t *)local_1c);
    if (ptVar2->tm_year < 0x66) {
      if ((ptVar2->tm_year == 0x65) && (8 < ptVar2->tm_mon)) {
        *(undefined4 *)(this + 0x168) = 0x14;
        iVar1 = 0;
      }
      else {
        iVar1 = 1;
      }
    }
    else {
      *(undefined4 *)(this + 0x168) = 0x14;
      iVar1 = 0;
    }
  }
  else if (*(int *)(this + 0xc0) == 7) {
    tVar3 = time((time_t *)0x0);
    local_24[0] = (undefined4)tVar3;
    ptVar2 = localtime((time_t *)local_24);
    if (ptVar2->tm_year < 0x67) {
      if ((ptVar2->tm_year == 0x66) && (2 < ptVar2->tm_mon)) {
        *(undefined4 *)(this + 0x168) = 0x14;
        iVar1 = 0;
      }
      else {
        iVar1 = 1;
      }
    }
    else {
      *(undefined4 *)(this + 0x168) = 0x14;
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 1;
  }
  return iVar1;
}

//===== 0x1002edeb =====

void FUN_1002edeb(void)

{
  FUN_1002edf5();
  return;
}

//===== 0x1002edf5 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_1002edf5(void)

{
  _DAT_10042530 = acos(-1.0);
  return;
}

//===== 0x1002ee0f =====

/* public: __thiscall Wvfm::Wvfm(int,int,char const *,enum Wvfm::DATASRC,enum Wvfm::Method) */

Wvfm * __thiscall
Wvfm::Wvfm(Wvfm *this,int param_1,int param_2,char *param_3,DATASRC param_4,Method param_5)

{
  int iVar1;
  size_t sVar2;
  undefined4 local_2c;
  uint local_24;
  int local_20;
  int local_1c;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x2ee0f  26  ??0Wvfm@@QAE@HHPBDW4DATASRC@0@W4Method@0@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_100374ec;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  Annotate::Annotate((Annotate *)(this + 4));
  local_8 = 0;
  *(int *)(this + 0xb0) = param_1;
  *(int *)(this + 0xb4) = param_2;
  *(undefined4 *)(this + 0xb8) = 1;
  *(undefined4 *)(this + 0xbc) = 0;
  *(DATASRC *)(this + 0xc0) = param_4;
  *(undefined4 *)(this + 0xc4) = 0;
  *(undefined4 *)(this + 200) = 0;
  *(undefined4 *)(this + 0xcc) = 0;
  *(undefined4 *)(this + 0xd0) = 0;
  *(undefined4 *)(this + 0xd4) = 0;
  *(Method *)(this + 0xd8) = param_5;
  *(undefined4 *)(this + 0x168) = 0;
  *(undefined4 *)(this + 0x16c) = 1;
  this[0x170] = (Wvfm)0x1;
  *(undefined4 *)(this + 0x174) = 1;
  *(undefined4 *)(this + 0x178) = 0;
  *(undefined4 *)(this + 0x1b0) = 0;
  *(undefined4 *)(this + 0x1b4) = 0;
  *(undefined4 *)(this + 0x1b8) = 0;
  *(undefined4 *)(this + 0x1bc) = 0;
  ObsInpSpec::ObsInpSpec((ObsInpSpec *)(this + 0x210));
  local_8 = CONCAT31(local_8._1_3_,1);
  *(undefined4 *)(this + 0x2f8) = 0;
  *(undefined4 *)(this + 0x2fc) = 0;
  *(undefined4 *)(this + 0x300) = 0;
  iVar1 = licenseOk(this);
  if (iVar1 != 0) {
    memset(this + 0xdc,0,6);
    if (param_3 != (char *)0x0) {
      for (local_24 = 0; sVar2 = strlen(param_3), local_24 < sVar2; local_24 = local_24 + 1) {
        iVar1 = toupper((int)param_3[local_24]);
        this[local_24 + 0xdc] = SUB41(iVar1,0);
      }
    }
    iVar1 = rows(this);
    dim(this,iVar1);
    for (local_1c = 1; local_1c <= *(int *)(this + 0xb0); local_1c = local_1c + 1) {
      *(undefined4 *)(*(int *)(this + 0x300) + local_1c * 4) = 0;
      for (local_20 = 1; local_20 <= *(int *)(this + 0xb4); local_20 = local_20 + 1) {
        iVar1 = *(int *)(*(int *)(this + 0xc4) + local_1c * 4);
        *(undefined4 *)(iVar1 + local_20 * 8) = 0;
        *(undefined4 *)(iVar1 + 4 + local_20 * 8) = 0;
      }
    }
    for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
      this[local_14 * 0x14 + 0x1d0] = (Wvfm)0x0;
      for (local_18 = 0; local_18 < 4; local_18 = local_18 + 1) {
        if (local_14 == local_18) {
          local_2c = 0x3ff00000;
        }
        else {
          local_2c = 0;
        }
        *(undefined4 *)(this + local_18 * 8 + local_14 * 0x20 + 0xe8) = 0;
        *(undefined4 *)(this + local_18 * 8 + local_14 * 0x20 + 0xec) = local_2c;
        *(undefined4 *)(this + local_18 * 4 + local_14 * 0x14 + 0x1c0) = 0;
      }
    }
    *(undefined4 *)(this + 0x17c) = 0;
    for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
      for (local_18 = 0; local_18 < 3; local_18 = local_18 + 1) {
        *(undefined4 *)(this + local_18 * 4 + local_14 * 0xc + 0x180) = 0;
      }
    }
    *(undefined4 *)(this + 0x168) = 1;
  }
  ExceptionList = local_10;
  return this;
}

//===== 0x1002f1a6 =====

/* public: __thiscall Wvfm::Wvfm(class Wvfm const &) */

Wvfm * __thiscall Wvfm::Wvfm(Wvfm *this,Wvfm *param_1)

{
  undefined4 local_20;
  int local_18;
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x2f1a6  25  ??0Wvfm@@QAE@ABV0@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037511;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *(undefined4 *)this = 0;
  Annotate::Annotate((Annotate *)(this + 4));
  local_8 = 0;
  *(undefined4 *)(this + 0xb0) = 0;
  *(undefined4 *)(this + 0xb4) = 0;
  *(undefined4 *)(this + 0xb8) = 0;
  *(undefined4 *)(this + 0xbc) = 0;
  *(undefined4 *)(this + 0xc0) = 0;
  *(undefined4 *)(this + 0xc4) = 0;
  *(undefined4 *)(this + 200) = 0;
  *(undefined4 *)(this + 0xcc) = 0;
  *(undefined4 *)(this + 0xd0) = 0;
  *(undefined4 *)(this + 0xd4) = 0;
  *(undefined4 *)(this + 0xd8) = 0;
  *(undefined4 *)(this + 0x168) = 0;
  *(undefined4 *)(this + 0x16c) = 1;
  this[0x170] = (Wvfm)0x1;
  *(undefined4 *)(this + 0x174) = 0;
  *(undefined4 *)(this + 0x178) = 0;
  *(undefined4 *)(this + 0x1b0) = 0;
  *(undefined4 *)(this + 0x1b4) = 0;
  *(undefined4 *)(this + 0x1b8) = 0;
  *(undefined4 *)(this + 0x1bc) = 0;
  ObsInpSpec::ObsInpSpec((ObsInpSpec *)(this + 0x210));
  local_8 = CONCAT31(local_8._1_3_,1);
  *(undefined4 *)(this + 0x2f8) = 0;
  *(undefined4 *)(this + 0x2fc) = 0;
  *(undefined4 *)(this + 0x300) = 0;
  memset(this + 0xdc,0,6);
  for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
    this[local_14 * 0x14 + 0x1d0] = (Wvfm)0x0;
    for (local_18 = 0; local_18 < 4; local_18 = local_18 + 1) {
      if (local_14 == local_18) {
        local_20 = 0x3ff00000;
      }
      else {
        local_20 = 0;
      }
      *(undefined4 *)(this + local_18 * 8 + local_14 * 0x20 + 0xe8) = 0;
      *(undefined4 *)(this + local_18 * 8 + local_14 * 0x20 + 0xec) = local_20;
      *(undefined4 *)(this + local_18 * 4 + local_14 * 0x14 + 0x1c0) = 0;
    }
  }
  *(undefined4 *)(this + 0x17c) = 0;
  for (local_14 = 0; local_14 < 4; local_14 = local_14 + 1) {
    for (local_18 = 0; local_18 < 3; local_18 = local_18 + 1) {
      *(undefined4 *)(this + local_18 * 4 + local_14 * 0xc + 0x180) = 0;
    }
  }
  operator=(this,param_1);
  ExceptionList = local_10;
  return this;
}

//===== 0x1002f45b =====

/* public: class Wvfm const & __thiscall Wvfm::operator=(class Wvfm const &) */

Wvfm * __thiscall Wvfm::operator=(Wvfm *this,Wvfm *param_1)

{
  int iVar1;
  int iVar2;
  double *pdVar3;
  int *piVar4;
  float *pfVar5;
  int iVar6;
  Wvfm *pWVar7;
  Wvfm *pWVar8;
  int local_c;
  int local_8;
  
                    /* 0x2f45b  55  ??4Wvfm@@QAEABV0@ABV0@@Z */
  if (this != param_1) {
    release(this);
    *(undefined4 *)this = *(undefined4 *)param_1;
    Annotate::operator=((Annotate *)(this + 4),(Annotate *)(param_1 + 4));
    *(undefined4 *)(this + 0x168) = *(undefined4 *)(param_1 + 0x168);
    *(undefined4 *)(this + 0xb0) = *(undefined4 *)(param_1 + 0xb0);
    *(undefined4 *)(this + 0xb4) = *(undefined4 *)(param_1 + 0xb4);
    *(undefined4 *)(this + 0x174) = *(undefined4 *)(param_1 + 0x174);
    *(undefined4 *)(this + 0x178) = *(undefined4 *)(param_1 + 0x178);
    *(undefined4 *)(this + 0xb8) = *(undefined4 *)(param_1 + 0xb8);
    *(undefined4 *)(this + 0xbc) = *(undefined4 *)(param_1 + 0xbc);
    *(undefined4 *)(this + 0xc0) = *(undefined4 *)(param_1 + 0xc0);
    *(undefined4 *)(this + 0xd8) = *(undefined4 *)(param_1 + 0xd8);
    *(undefined4 *)(this + 0x16c) = *(undefined4 *)(param_1 + 0x16c);
    this[0x170] = param_1[0x170];
    pWVar7 = param_1 + 0x17c;
    pWVar8 = this + 0x17c;
    for (iVar6 = 0xd; iVar6 != 0; iVar6 = iVar6 + -1) {
      *(undefined4 *)pWVar8 = *(undefined4 *)pWVar7;
      pWVar7 = pWVar7 + 4;
      pWVar8 = pWVar8 + 4;
    }
    *(undefined4 *)(this + 0x1b0) = *(undefined4 *)(param_1 + 0x1b0);
    *(undefined4 *)(this + 0x1b4) = *(undefined4 *)(param_1 + 0x1b4);
    *(undefined4 *)(this + 0x1b8) = *(undefined4 *)(param_1 + 0x1b8);
    ObsInpSpec::operator=((ObsInpSpec *)(this + 0x210),(ObsInpSpec *)(param_1 + 0x210));
    *(undefined4 *)(this + 0x1bc) = *(undefined4 *)(param_1 + 0x1bc);
    *(undefined4 *)(this + 0x2f8) = *(undefined4 *)(param_1 + 0x2f8);
    *(undefined4 *)(this + 0x2fc) = *(undefined4 *)(param_1 + 0x2fc);
    if (((*(int *)(param_1 + 0xc4) != 0) && (*(int *)(this + 0xb0) != 0)) &&
       (*(int *)(this + 0xb4) != 0)) {
      iVar6 = dim(this,*(int *)(this + 0xb0));
      if (iVar6 == 0) {
        *(undefined4 *)(this + 0x168) = 2;
        return this;
      }
      for (local_8 = 1; local_8 <= *(int *)(this + 0xb0); local_8 = local_8 + 1) {
        *(undefined4 *)(*(int *)(this + 0x300) + local_8 * 4) =
             *(undefined4 *)(*(int *)(param_1 + 0x300) + local_8 * 4);
        for (local_c = 1; local_c <= *(int *)(this + 0xb4); local_c = local_c + 1) {
          iVar6 = *(int *)(*(int *)(param_1 + 0xc4) + local_8 * 4);
          iVar1 = *(int *)(*(int *)(this + 0xc4) + local_8 * 4);
          *(undefined4 *)(iVar1 + local_c * 8) = *(undefined4 *)(iVar6 + local_c * 8);
          *(undefined4 *)(iVar1 + 4 + local_c * 8) = *(undefined4 *)(iVar6 + 4 + local_c * 8);
        }
      }
    }
    strncpy((char *)(this + 0xdc),(char *)(param_1 + 0xdc),6);
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      this[local_8 * 0x14 + 0x1d0] = param_1[local_8 * 0x14 + 0x1d0];
      for (local_c = 0; local_c < 4; local_c = local_c + 1) {
        *(undefined4 *)(this + local_c * 8 + local_8 * 0x20 + 0xe8) =
             *(undefined4 *)(param_1 + local_c * 8 + local_8 * 0x20 + 0xe8);
        *(undefined4 *)(this + local_c * 8 + local_8 * 0x20 + 0xec) =
             *(undefined4 *)(param_1 + local_c * 8 + local_8 * 0x20 + 0xec);
        *(undefined4 *)(this + local_c * 4 + local_8 * 0x14 + 0x1c0) =
             *(undefined4 *)(param_1 + local_c * 4 + local_8 * 0x14 + 0x1c0);
      }
    }
    iVar6 = rows(this);
    if (((*(int *)(param_1 + 200) != 0) && (*(int *)(param_1 + 0xcc) != 0)) &&
       ((*(int *)(param_1 + 0xd0) != 0 && (*(int *)(param_1 + 0xd4) != 0)))) {
      pdVar3 = dvector(1,iVar6);
      *(double **)(this + 200) = pdVar3;
      pdVar3 = dvector(1,iVar6);
      *(double **)(this + 0xd0) = pdVar3;
      piVar4 = ivector(1,iVar6);
      *(int **)(this + 0xcc) = piVar4;
      pfVar5 = vector(1,iVar6);
      *(float **)(this + 0xd4) = pfVar5;
      if (((*(int *)(this + 200) == 0) || (*(int *)(this + 0xcc) == 0)) ||
         ((*(int *)(this + 0xd0) == 0 || (*(int *)(this + 0xd4) == 0)))) {
        *(undefined4 *)(this + 0x168) = 2;
      }
      else {
        for (local_8 = 1; local_8 <= iVar6; local_8 = local_8 + 1) {
          iVar1 = *(int *)(param_1 + 200);
          iVar2 = *(int *)(this + 200);
          *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
          *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
          *(undefined4 *)(*(int *)(this + 0xcc) + local_8 * 4) =
               *(undefined4 *)(*(int *)(param_1 + 0xcc) + local_8 * 4);
          iVar1 = *(int *)(param_1 + 0xd0);
          iVar2 = *(int *)(this + 0xd0);
          *(undefined4 *)(iVar2 + local_8 * 8) = *(undefined4 *)(iVar1 + local_8 * 8);
          *(undefined4 *)(iVar2 + 4 + local_8 * 8) = *(undefined4 *)(iVar1 + 4 + local_8 * 8);
          *(undefined4 *)(*(int *)(this + 0xd4) + local_8 * 4) =
               *(undefined4 *)(*(int *)(param_1 + 0xd4) + local_8 * 4);
        }
      }
    }
  }
  return this;
}

//===== 0x1002f966 =====

/* private: void __thiscall Wvfm::release(void) */

void __thiscall Wvfm::release(Wvfm *this)

{
  int iVar1;
  
                    /* 0x2f966  336  ?release@Wvfm@@AAEXXZ */
  iVar1 = rows(this);
  if (*(int *)(this + 0xc4) != 0) {
    free_dmatrix(*(double ***)(this + 0xc4),1,*(long *)(this + 0xb0),1,*(long *)(this + 0xb4));
    *(undefined4 *)(this + 0xc4) = 0;
  }
  if (*(int *)(this + 0x300) != 0) {
    free_vector(*(float **)(this + 0x300),1,*(long *)(this + 0xb0));
    *(undefined4 *)(this + 0x300) = 0;
  }
  if (*(int *)(this + 200) != 0) {
    free_dvector(*(double **)(this + 200),1,iVar1);
    *(undefined4 *)(this + 200) = 0;
  }
  if (*(int *)(this + 0xcc) != 0) {
    free_ivector(*(int **)(this + 0xcc),1,iVar1);
    *(undefined4 *)(this + 0xcc) = 0;
  }
  if (*(int *)(this + 0xd0) != 0) {
    free_dvector(*(double **)(this + 0xd0),1,iVar1);
    *(undefined4 *)(this + 0xd0) = 0;
  }
  if (*(int *)(this + 0xd4) != 0) {
    free_vector(*(float **)(this + 0xd4),1,iVar1);
    *(undefined4 *)(this + 0xd4) = 0;
  }
  return;
}

//===== 0x1002fabc =====

/* public: __thiscall Wvfm::~Wvfm(void) */

void __thiscall Wvfm::~Wvfm(Wvfm *this)

{
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
                    /* 0x2fabc  41  ??1Wvfm@@QAE@XZ */
  puStack_c = &LAB_10037536;
  local_10 = ExceptionList;
  local_8 = 1;
  ExceptionList = &local_10;
  release(this);
  local_8 = local_8 & 0xffffff00;
  ObsInpSpec::~ObsInpSpec((ObsInpSpec *)(this + 0x210));
  local_8 = 0xffffffff;
  Annotate::~Annotate((Annotate *)(this + 4));
  ExceptionList = local_10;
  return;
}

//===== 0x1002fb19 =====

/* private: int __thiscall Wvfm::bgnEnd(struct TestOptions const &) */

int __thiscall Wvfm::bgnEnd(Wvfm *this,TestOptions *param_1)

{
  int iVar1;
  int local_398;
  LMConvert local_38c [888];
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x2fb19  90  ?bgnEnd@Wvfm@@AAEHABUTestOptions@@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003754c;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  if (((1 < *(int *)(this + 0xb8)) &&
      (ExceptionList = &local_10, *(int *)(this + 0xb8) < *(int *)(this + 0xbc))) &&
     (ExceptionList = &local_10, iVar1 = rows(this), *(int *)(this + 0xbc) <= iVar1)) {
    *(undefined4 *)(this + 0x174) = *(undefined4 *)(this + 0xb8);
    *(undefined4 *)(this + 0x178) = *(undefined4 *)(this + 0xbc);
    *(undefined4 *)(this + 0x1b4) = *(undefined4 *)(this + 0xb8);
    *(int *)(this + 0x1b8) = (*(int *)(this + 0xb8) + 1 + *(int *)(this + 0xbc)) / 2;
    ExceptionList = local_10;
    return 1;
  }
  FUN_100092e0(local_38c,this,(uint *)param_1);
  local_8 = 0;
  iVar1 = LMConvert::nout(local_38c);
  *(int *)(this + 0xb8) = iVar1;
  *(undefined4 *)(this + 0x174) = *(undefined4 *)(this + 0xb8);
  iVar1 = Annotate::getCFlen((Annotate *)local_38c);
  *(int *)(this + 0xbc) = iVar1;
  *(undefined4 *)(this + 0x178) = *(undefined4 *)(this + 0xbc);
  *(undefined4 *)(this + 0x1b4) = *(undefined4 *)(this + 0xb8);
  *(int *)(this + 0x1b8) = (*(int *)(this + 0xb8) + 1 + *(int *)(this + 0xbc)) / 2;
  if ((*(int *)(this + 0xb8) < 2) || (*(int *)(this + 0xbc) < *(int *)(this + 0xb8))) {
    local_398 = 0;
  }
  else {
    local_398 = 1;
  }
  local_14 = local_398;
  if (local_398 != 1) {
    *(undefined4 *)(this + 0x168) = 0xb;
  }
  local_8 = 0xffffffff;
  FUN_10009624((int)local_38c);
  ExceptionList = local_10;
  return local_398;
}

//===== 0x1002fd55 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Wvfm::fbbls_(int,double *,enum Wvfm::DIRECTION_,float &)const  */

void __thiscall
Wvfm::fbbls_(Wvfm *this,int param_1,double *param_2,DIRECTION_ param_3,float *param_4)

{
  int iVar1;
  void *pvVar2;
  float *pfVar3;
  int iVar4;
  double dVar5;
  undefined8 local_c8;
  undefined8 local_bc;
  undefined8 local_ac;
  float local_74;
  float local_70;
  double local_6c;
  undefined8 local_50;
  double local_48;
  int local_3c;
  double local_38;
  int local_30;
  int local_2c;
  undefined8 local_18;
  int local_10;
  double local_c;
  
                    /* 0x2fd55  155  ?fbbls_@Wvfm@@ABEXHPANW4DIRECTION_@1@AAM@Z */
  local_10 = 1;
  pvVar2 = operator_new(0x328);
  for (local_2c = 1; local_2c < 0x65; local_2c = local_2c + 1) {
    dVar5 = exp((double)local_2c / 75.0);
    *(double *)((int)pvVar2 + local_2c * 8) = dVar5 - _DAT_10038e68;
  }
  if (param_3 == 1) {
    local_30 = *(int *)(this + 0xb8);
    local_3c = *(int *)(this + 0xb8) + 1;
    iVar4 = *(int *)(this + 0xbc) + 1;
    pfVar3 = vector(1,*(long *)(this + 0xbc));
    local_74 = 0.0;
    local_70 = 0.0;
    *param_4 = 5.0;
    for (local_2c = *(int *)(this + 0xb8); local_2c <= *(int *)(this + 0xbc);
        local_2c = local_2c + 1) {
      pfVar3[local_2c] =
           (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + local_2c * 4) + param_1 * 8);
      local_74 = local_74 + pfVar3[local_2c];
    }
    if (_DAT_10038e70 != local_74) {
      qsort(pfVar3 + *(int *)(this + 0xb8),(*(int *)(this + 0xbc) - *(int *)(this + 0xb8)) + 1,4,
            FUN_10030376);
      for (local_2c = *(int *)(this + 0xb8); local_2c <= *(int *)(this + 0xbc);
          local_2c = local_2c + 1) {
        local_70 = pfVar3[local_2c] / local_74 + local_70;
        if (_DAT_10038e74 <= local_70) {
          *param_4 = pfVar3[local_2c];
          break;
        }
      }
    }
    free_vector(pfVar3,1,*(long *)(this + 0xbc));
  }
  else {
    local_30 = *(int *)(this + 0xbc);
    local_3c = *(int *)(this + 0xbc) + -1;
    iVar4 = *(int *)(this + 0xb8) + -1;
  }
  iVar1 = *(int *)(*(int *)(this + 0xc4) + local_30 * 4);
  local_50 = (double)CONCAT44(*(undefined4 *)(iVar1 + 4 + param_1 * 8),
                              *(undefined4 *)(iVar1 + param_1 * 8));
  local_2c = local_3c;
  while ((local_2c != local_3c + param_3 * 10 &&
         (iVar1 = *(int *)(*(int *)(this + 0xc4) + local_2c * 4),
         local_50 = (double)CONCAT44(*(undefined4 *)(iVar1 + 4 + param_1 * 8),
                                     *(undefined4 *)(iVar1 + param_1 * 8)),
         local_50 <= (double)*param_4))) {
    local_2c = local_2c + param_3;
  }
  if ((float)local_50 < *param_4) {
    local_50 = (double)*param_4;
  }
  local_48 = local_50 / _DAT_10038e78;
  dVar5 = exp(1.0);
  local_48 = local_48 / (dVar5 - _DAT_10038e68);
  for (; local_3c != iVar4; local_3c = local_3c + param_3) {
    local_10 = local_10 + 1;
    local_c = local_48 * *(double *)((int)pvVar2 + local_10 * 8) + local_50;
    iVar1 = *(int *)(*(int *)(this + 0xc4) + local_3c * 4);
    local_18 = (double)CONCAT44(*(undefined4 *)(iVar1 + 4 + param_1 * 8),
                                *(undefined4 *)(iVar1 + param_1 * 8));
    if (local_18 <= (double)*param_4) {
      local_18 = local_c + _DAT_10038e68;
    }
    if ((local_18 <= local_c) || (99 < local_10)) {
      if ((99 < local_10) && (local_c < local_18)) {
        local_18 = local_c;
      }
      local_6c = (local_18 - local_50) / (double)(local_3c - local_30);
      local_38 = local_18 - (double)local_3c * local_6c;
      local_50 = local_18;
      for (local_2c = local_30; local_2c != local_3c; local_2c = local_2c + param_3) {
        local_ac = (double)local_2c * local_6c + local_38;
        if (param_3 != 1) {
          local_ac = sqrt(local_ac * param_2[local_2c]);
        }
        *(undefined4 *)(param_2 + local_2c) = (undefined4)local_ac;
        *(undefined4 *)((int)param_2 + local_2c * 8 + 4) = local_ac._4_4_;
      }
      local_30 = local_3c;
      local_10 = 1;
      local_48 = local_18 / _DAT_10038e78;
      dVar5 = exp(1.0);
      local_48 = local_48 / (dVar5 - _DAT_10038e68);
    }
  }
  local_3c = local_3c - param_3;
  if (local_3c == local_30) {
    local_bc = (double)local_3c * local_6c + local_38;
    if (param_3 != 1) {
      local_bc = sqrt(local_bc * param_2[local_3c]);
    }
    *(undefined4 *)(param_2 + local_3c) = (undefined4)local_bc;
    *(undefined4 *)((int)param_2 + local_3c * 8 + 4) = local_bc._4_4_;
  }
  else {
    if (local_c < local_18) {
      local_18 = local_c;
    }
    dVar5 = (local_18 - local_50) / (double)(local_3c - local_30);
    for (local_2c = local_30; local_2c != local_3c + param_3; local_2c = local_2c + param_3) {
      local_c8 = (double)local_2c * dVar5 + (local_18 - (double)local_3c * dVar5);
      if (param_3 != 1) {
        local_c8 = sqrt(local_c8 * param_2[local_2c]);
      }
      *(undefined4 *)(param_2 + local_2c) = (undefined4)local_c8;
      *(undefined4 *)((int)param_2 + local_2c * 8 + 4) = local_c8._4_4_;
    }
  }
  operator_delete(pvVar2);
  return;
}

//===== 0x10030376 =====

undefined4 __cdecl FUN_10030376(float *param_1,float *param_2)

{
  undefined4 uVar1;
  
  if (*param_2 <= *param_1) {
    if (*param_1 <= *param_2) {
      uVar1 = 0;
    }
    else {
      uVar1 = 1;
    }
  }
  else {
    uVar1 = 0xffffffff;
  }
  return uVar1;
}

//===== 0x100303b8 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: void __thiscall Wvfm::bestBaseline_(void) */

void __thiscall Wvfm::bestBaseline_(Wvfm *this)

{
  int iVar1;
  undefined8 local_1c;
  float local_14;
  int local_10;
  int local_c;
  double *local_8;
  
                    /* 0x303b8  89  ?bestBaseline_@Wvfm@@AAEXXZ */
  local_8 = dvector(1,*(long *)(this + 0xbc));
  local_c = 1;
  while( true ) {
    iVar1 = cols(this);
    if (iVar1 < local_c) {
      free_dvector(local_8,1,*(long *)(this + 0xbc));
      return;
    }
    fbbls_(this,local_c,local_8,1,&local_14);
    fbbls_(this,local_c,local_8,0xffffffff,&local_14);
    iVar1 = FUN_10030505((int)local_8,*(int *)(this + 0xb8),*(int *)(this + 0xbc));
    if (iVar1 != 0) break;
    for (local_10 = *(int *)(this + 0xb8); local_10 <= *(int *)(this + 0xbc);
        local_10 = local_10 + 1) {
      local_1c = *(double *)(*(int *)(*(int *)(this + 0xc4) + local_10 * 4) + local_c * 8) -
                 local_8[local_10];
      if (local_1c < _DAT_10038e80) {
        local_1c = 0.0;
      }
      iVar1 = *(int *)(*(int *)(this + 0xc4) + local_10 * 4);
      *(undefined4 *)(iVar1 + local_c * 8) = (undefined4)local_1c;
      *(undefined4 *)(iVar1 + 4 + local_c * 8) = local_1c._4_4_;
    }
    local_c = local_c + 1;
  }
  *(undefined4 *)(this + 0x168) = 2;
  return;
}

//===== 0x10030505 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __cdecl FUN_10030505(int param_1,int param_2,int param_3)

{
  int iVar1;
  undefined4 uVar2;
  byte bVar3;
  int iVar4;
  int iVar5;
  double *pdVar6;
  double *pdVar7;
  double *pdVar8;
  undefined4 uVar9;
  int iVar10;
  ulong uVar11;
  double dVar12;
  double dVar13;
  undefined4 local_70;
  undefined4 uStack_6c;
  double local_50;
  double local_38;
  double local_30;
  double local_24;
  int local_18;
  double local_14;
  double local_c;
  
  iVar1 = param_1 + -8 + param_2 * 8;
  iVar4 = param_3 - param_2;
  iVar5 = iVar4 + 1;
  dVar12 = log((double)(iVar5 * 3 + 0xf8));
  dVar13 = log(2.0);
  ceil(dVar12 / dVar13);
  bVar3 = ftol();
  uVar11 = 1 << (bVar3 & 0x1f);
  pdVar6 = dvector(1,uVar11 << 1);
  pdVar7 = dvector(1,uVar11 << 1);
  pdVar8 = dvector(1,iVar5);
  if (((pdVar6 == (double *)0x0) || (pdVar7 == (double *)0x0)) || (pdVar8 == (double *)0x0)) {
    if (pdVar6 != (double *)0x0) {
      free_dvector(pdVar6,1,uVar11 << 1);
    }
    if (pdVar7 != (double *)0x0) {
      free_dvector(pdVar7,1,uVar11 << 1);
    }
    if (pdVar8 != (double *)0x0) {
      free_dvector(pdVar8,1,iVar5);
    }
    uVar9 = 1;
  }
  else {
    for (local_18 = 1; local_18 <= (int)(uVar11 * 2); local_18 = local_18 + 1) {
      *(undefined4 *)(pdVar7 + local_18) = 0;
      *(undefined4 *)((int)pdVar7 + local_18 * 8 + 4) = 0;
      *(undefined4 *)(pdVar6 + local_18) = 0;
      *(undefined4 *)((int)pdVar6 + local_18 * 8 + 4) = 0;
    }
    for (local_18 = 1; local_18 <= iVar5; local_18 = local_18 + 1) {
      uVar9 = *(undefined4 *)(iVar1 + local_18 * 8);
      uVar2 = *(undefined4 *)(iVar1 + 4 + local_18 * 8);
      iVar10 = (iVar4 + 2) - local_18;
      *(undefined4 *)(pdVar6 + iVar10 * 2 + -1) = uVar9;
      *(undefined4 *)((int)pdVar6 + iVar10 * 0x10 + -4) = uVar2;
      *(undefined4 *)(pdVar6 + (iVar5 + local_18) * 2 + -1) = uVar9;
      *(undefined4 *)((int)pdVar6 + (iVar5 + local_18) * 0x10 + -4) = uVar2;
      iVar10 = (iVar5 * 3 + 1) - local_18;
      *(undefined4 *)(pdVar6 + iVar10 * 2 + -1) = uVar9;
      *(undefined4 *)((int)pdVar6 + iVar10 * 0x10 + -4) = uVar2;
    }
    dfour1(pdVar6,uVar11,1);
    for (local_18 = 1; local_18 < 0x7e; local_18 = local_18 + 1) {
      dVar12 = cos(((double)(local_18 + -1) * _DAT_10042530) / _DAT_10038e88);
      dVar12 = ((dVar12 + _DAT_10038e68) * _DAT_10038e90) / _DAT_10038e88;
      local_70 = SUB84(dVar12,0);
      *(undefined4 *)(pdVar7 + local_18 * 2 + -1) = local_70;
      uStack_6c = (undefined4)((ulonglong)dVar12 >> 0x20);
      *(undefined4 *)((int)pdVar7 + local_18 * 0x10 + -4) = uStack_6c;
      if (local_18 != 1) {
        iVar10 = (uVar11 - local_18) * 2;
        *(undefined4 *)(pdVar7 + iVar10 + 3) = local_70;
        *(undefined4 *)((int)pdVar7 + (iVar10 + 4) * 8 + -4) = uStack_6c;
      }
    }
    dfour1(pdVar7,uVar11,1);
    FUN_10034b00((int)pdVar6,(int)pdVar7,(int)pdVar7,uVar11);
    dfour1(pdVar7,uVar11,-1);
    for (local_18 = 1; local_18 <= iVar5; local_18 = local_18 + 1) {
      pdVar8[local_18] = pdVar7[(iVar5 + local_18) * 2 + -1] / (double)(int)uVar11;
    }
    local_24 = 0.0;
    local_30 = 0.0;
    local_50 = 0.0;
    local_c = 0.0;
    local_14 = 0.0;
    local_38 = 0.0;
    for (local_18 = 1; local_18 <= iVar5 / 10; local_18 = local_18 + 1) {
      dVar12 = pdVar8[local_18] - *(double *)(iVar1 + local_18 * 8);
      dVar13 = pdVar8[(iVar4 + 2) - local_18] - *(double *)(iVar1 + ((iVar4 + 2) - local_18) * 8);
      if (_DAT_10038e80 < dVar12) {
        local_50 = local_50 + _DAT_10038e68;
        local_24 = (double)local_18 + local_24;
        local_30 = local_30 + dVar12;
      }
      if (_DAT_10038e80 < dVar13) {
        local_38 = local_38 + _DAT_10038e68;
        local_c = (double)((iVar4 + 2) - local_18) + local_c;
        local_14 = local_14 + dVar13;
      }
    }
    if (_DAT_10038e80 == local_50) {
      local_24 = (double)local_18;
      local_30 = 0.0;
    }
    else {
      local_24 = local_24 / local_50;
      local_30 = local_30 / local_50;
    }
    if (_DAT_10038e80 == local_38) {
      local_c = (double)iVar5;
      local_14 = 0.0;
    }
    else {
      local_c = local_c / local_38;
      local_14 = local_14 / local_38;
    }
    dVar12 = (local_14 - local_30) / (local_c - local_24);
    for (local_18 = 1; local_18 <= iVar5; local_18 = local_18 + 1) {
      *(double *)(iVar1 + local_18 * 8) =
           pdVar8[local_18] - ((double)local_18 * dVar12 + (local_14 - dVar12 * local_c));
    }
    free_dvector(pdVar6,1,uVar11 << 1);
    free_dvector(pdVar7,1,uVar11 << 1);
    free_dvector(pdVar8,1,iVar5);
    uVar9 = 0;
  }
  return uVar9;
}

//===== 0x10030a2c =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* private: int __thiscall Wvfm::specSep(struct TestOptions const &) */

int __thiscall Wvfm::specSep(Wvfm *this,TestOptions *param_1)

{
  float fVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  int iVar10;
  int iVar11;
  float10 fVar12;
  float *local_558;
  int local_554;
  float *local_53c;
  int local_538;
  undefined8 uStack_534;
  int local_50c;
  int local_508;
  void *local_504;
  int local_500;
  double **local_4fc;
  int local_4f8;
  int local_4f4;
  ObsInpSpec *local_4f0;
  undefined8 local_4ec;
  int local_4cc;
  int local_4c8;
  int local_4c4;
  int local_4c0;
  Wvfm local_4bc [1112];
  int local_64;
  int local_60;
  double **local_5c;
  float local_58;
  int local_54;
  undefined1 local_50 [60];
  int local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x30a2c  406  ?specSep@Wvfm@@AAEHABUTestOptions@@@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_1003756b;
  local_10 = ExceptionList;
  if ((((*(int *)(this + 0xb8) == 0) || (*(int *)(this + 0xbc) == 0)) ||
      (*(int *)(this + 0xbc) < *(int *)(this + 0xb8))) ||
     ((*(int *)(this + 0xb0) == 0 || (*(int *)(this + 0xb4) == 0)))) {
    *(undefined4 *)(this + 0x168) = 7;
    iVar2 = 0;
  }
  else {
    ExceptionList = &local_10;
    bestBaseline_(this);
    if (*(int *)this != 0) {
      Annotate::setTraces((Annotate *)(this + 4),1,*(double ***)(this + 0xc4));
      iVar2 = Annotate::getPsdSz((Annotate *)(this + 4));
      local_5c = dmatrix(1,4,1,iVar2);
      iVar2 = Annotate::getPsdSz((Annotate *)(this + 4));
      psd(this,local_5c,iVar2);
      Annotate::setPsd1((Annotate *)(this + 4),local_5c);
    }
    if (this[0x170] != (Wvfm)0x0) {
      FUN_10027e70(local_4bc,this);
      local_8 = 0;
      iVar2 = annotate(local_4bc);
      if (iVar2 != 9) {
        iVar2 = annotate(local_4bc);
        switch(iVar2) {
        case 0:
          *(undefined4 *)(this + 0x168) = 0xc;
          break;
        case 1:
          *(undefined4 *)(this + 0x168) = 2;
          break;
        case 2:
          *(undefined4 *)(this + 0x168) = 0xd;
          break;
        case 3:
          *(undefined4 *)(this + 0x168) = 0xe;
          break;
        case 4:
          *(undefined4 *)(this + 0x168) = 0xe;
          break;
        case 5:
          *(undefined4 *)(this + 0x168) = 0xf;
          break;
        case 6:
          *(undefined4 *)(this + 0x168) = 0x10;
          break;
        case 7:
          *(undefined4 *)(this + 0x168) = 0x11;
          break;
        case 8:
          *(undefined4 *)(this + 0x168) = 0x12;
          break;
        default:
          *(undefined4 *)(this + 0x168) = 0xc;
        }
        if (*(int *)this != 0) {
          Annotate::setSpecSepDepth((Annotate *)(this + 4),-1);
        }
        local_8 = 0xffffffff;
        FUN_100285a5((int)local_4bc);
        ExceptionList = local_10;
        return 0;
      }
      if (*(int *)this != 0) {
        iVar2 = FUN_10032df0((int)local_4bc);
        Annotate::setSpecSepDepth((Annotate *)(this + 4),iVar2);
      }
      local_4c0 = FUN_10032d90((int)local_4bc);
      if (local_4c0 != 0) {
        local_64 = 1;
        while (iVar2 = cols(this), local_64 <= iVar2) {
          local_60 = 1;
          while (iVar2 = cols(this), local_60 <= iVar2) {
            fVar12 = FUN_10032d40((int)local_4bc,local_64,local_60);
            *(double *)(this + local_60 * 8 + (local_64 + -1) * 0x20 + 0xe0) = (double)fVar12;
            local_60 = local_60 + 1;
          }
          local_64 = local_64 + 1;
        }
        for (local_64 = 0; local_64 < 4; local_64 = local_64 + 1) {
          local_4cc = FUN_10032d70(local_4bc,local_64);
          local_4c4 = FUN_10032db0(local_4bc,local_64);
          local_4c8 = FUN_10032dd0(local_4bc,local_64);
          for (local_60 = 0; local_60 < 4; local_60 = local_60 + 1) {
            ObsInpSpec::ratio((ObsInpSpec *)(this + 0x210),local_64,local_60,
                              *(float *)(local_4cc + local_60 * 4),local_4c0,local_4c4,local_4c8);
          }
        }
      }
      local_8 = 0xffffffff;
      FUN_100285a5((int)local_4bc);
    }
    for (local_14 = *(int *)(this + 0xb8); local_14 <= *(int *)(this + 0xbc);
        local_14 = local_14 + 1) {
      local_54 = 0;
      while (iVar3 = cols(this), iVar2 = local_54, local_54 < iVar3) {
        *(undefined4 *)(&local_4ec + local_54) = 0;
        *(undefined4 *)((int)&local_4ec + iVar2 * 8 + 4) = 0;
        local_58 = 1.4013e-45;
        while (iVar2 = cols(this), (int)local_58 <= iVar2) {
          (&local_4ec)[local_54] =
               *(double *)(*(int *)(*(int *)(this + 0xc4) + local_14 * 4) + (int)local_58 * 8) *
               *(double *)(this + local_54 * 8 + ((int)local_58 + -1) * 0x20 + 0xe8) +
               (double)(&local_4ec)[local_54];
          local_58 = (float)((int)local_58 + 1);
        }
        local_54 = local_54 + 1;
      }
      local_58 = 1.4013e-45;
      while (iVar2 = cols(this), (int)local_58 <= iVar2) {
        iVar2 = *(int *)(*(int *)(this + 0xc4) + local_14 * 4);
        *(int *)(iVar2 + (int)local_58 * 8) = (&local_4f4)[(int)local_58 * 2];
        *(ObsInpSpec **)(iVar2 + 4 + (int)local_58 * 8) = (&local_4f0)[(int)local_58 * 2];
        local_58 = (float)((int)local_58 + 1);
      }
    }
    for (local_14 = *(int *)(this + 0xb8); local_14 <= *(int *)(this + 0xbc);
        local_14 = local_14 + 1) {
      local_58 = 1.4013e-45;
      while (iVar2 = cols(this), (int)local_58 <= iVar2) {
        if (*(double *)(*(int *)(*(int *)(this + 0xc4) + local_14 * 4) + (int)local_58 * 8) <
            _DAT_10038e80) {
          iVar2 = *(int *)(*(int *)(this + 0xc4) + local_14 * 4);
          *(undefined4 *)(iVar2 + (int)local_58 * 8) = 0;
          *(undefined4 *)(iVar2 + 4 + (int)local_58 * 8) = 0;
        }
        local_58 = (float)((int)local_58 + 1);
      }
    }
    if (*(int *)this != 0) {
      Annotate::setCFOrdr((Annotate *)(this + 4),(char *)(this + 0xdc));
      Annotate::setTraces((Annotate *)(this + 4),2,*(double ***)(this + 0xc4));
      if (*(int *)(this + 0xc0) == 2) {
        CarlFullerMeasurement(this);
        local_4f0 = ispec(this);
        local_4f4 = ObsInpSpec::cfzones(local_4f0);
        if (0 < local_4f4) {
          Annotate::setCFlen((Annotate *)(this + 4),local_4f4);
          for (local_4f8 = 0; local_4f8 < local_4f4; local_4f8 = local_4f8 + 1) {
            iVar2 = ObsInpSpec::cfnoise(local_4f0,3,local_4f8);
            iVar3 = ObsInpSpec::cfsignal(local_4f0,3,local_4f8);
            iVar4 = ObsInpSpec::cfnoise(local_4f0,2,local_4f8);
            iVar5 = ObsInpSpec::cfsignal(local_4f0,2,local_4f8);
            iVar6 = ObsInpSpec::cfnoise(local_4f0,1,local_4f8);
            iVar7 = ObsInpSpec::cfsignal(local_4f0,1,local_4f8);
            iVar8 = ObsInpSpec::cfnoise(local_4f0,0,local_4f8);
            iVar9 = ObsInpSpec::cfsignal(local_4f0,0,local_4f8);
            iVar10 = ObsInpSpec::cfend(local_4f0,local_4f8);
            iVar11 = ObsInpSpec::cfbgn(local_4f0,local_4f8);
            Annotate::setCFData((Annotate *)(this + 4),local_4f8,iVar11,iVar10,iVar9,iVar8,iVar7,
                                iVar6,iVar5,iVar4,iVar3,iVar2);
          }
        }
      }
    }
    FUN_10013a80(local_50,this,0);
    local_8 = 1;
    if (*(int *)this != 0) {
      Annotate::setTraces((Annotate *)(this + 4),3,*(double ***)(this + 0xc4));
    }
    if (*(int *)this != 0) {
      Annotate::qualifySST
                ((Annotate *)(this + 4),*(double ***)(this + 0xc4),*(int *)(this + 0xb8),
                 *(int *)(this + 0xbc));
      Annotate::measRawRes
                ((Annotate *)(this + 4),*(double ***)(this + 0xc4),*(int *)(this + 0xb8),
                 *(int *)(this + 0xbc));
      iVar2 = Annotate::getPsdSz((Annotate *)(this + 4));
      local_4fc = dmatrix(1,4,1,iVar2);
      iVar2 = Annotate::getPsdSz((Annotate *)(this + 4));
      psd(this,local_4fc,iVar2);
      Annotate::setPsd2((Annotate *)(this + 4),local_4fc);
    }
    if ((*(uint *)param_1 >> 7 & 1) == 1) {
      local_504 = operator_new(*(int *)(this + 0xbc) * 8 + 0x10);
      iVar2 = *(int *)(this + 0xb8);
      local_538 = *(int *)(this + 0xbc);
      local_50c = iVar2;
      if (1999 < local_538 - iVar2) {
        local_50c = iVar2 + 1000;
        local_538 = iVar2 + 2000;
      }
      for (local_14 = local_50c; local_14 <= local_538; local_14 = local_14 + 1) {
        local_53c = (float *)((int)local_504 + local_14 * 8);
        iVar2 = *(int *)(this + 0xc4);
        local_53c[1] = 1.4013e-45;
        *local_53c = (float)*(double *)(*(int *)(iVar2 + local_14 * 4) + 8);
        for (local_58 = 2.8026e-45; (int)local_58 < 5; local_58 = (float)((int)local_58 + 1)) {
          if (*local_53c <
              (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + local_14 * 4) + (int)local_58 * 8)
             ) {
            iVar2 = *(int *)(this + 0xc4);
            local_53c[1] = local_58;
            *local_53c = (float)*(double *)(*(int *)(iVar2 + local_14 * 4) + (int)local_58 * 8);
          }
        }
      }
      qsort((void *)((int)local_504 + local_50c * 8),(local_538 - local_50c) + 1,8,FUN_100316af);
      local_500 = local_50c;
      local_508 = local_50c;
      for (local_58 = 1.4013e-45; fVar1 = local_58, local_508 = local_500, (int)local_58 < 5;
          local_58 = (float)((int)local_58 + 1)) {
        while ((local_508 <= local_538 &&
               (local_58 == *(float *)((int)local_504 + local_508 * 8 + 4)))) {
          local_508 = local_508 + 1;
        }
        if (local_500 + 1 < local_508) {
          qsort((void *)((int)local_504 + local_500 * 8),local_508 - local_500,8,FUN_100316c0);
          (&uStack_534)[(int)local_58] =
               (double)((float)_DAT_10038e98 /
                       *(float *)((int)local_504 +
                                 (local_500 + ((local_508 - local_500) * 0x4b) / 100) * 8));
        }
        else if (local_500 < local_508) {
          (&uStack_534)[(int)local_58] =
               (double)((float)_DAT_10038e98 / *(float *)((int)local_504 + local_500 * 8));
        }
        else {
          if ((int)local_58 < 2) {
            local_558 = (float *)0x0;
            local_554 = 0x3ff00000;
          }
          else {
            local_558 = (&local_53c)[(int)local_58 * 2];
            local_554 = (&local_538)[(int)local_58 * 2];
          }
          *(float **)(&uStack_534 + (int)local_58) = local_558;
          *(int *)((int)&uStack_534 + (int)fVar1 * 8 + 4) = local_554;
        }
        local_500 = local_508;
        for (local_14 = *(int *)(this + 0xb8); local_14 <= *(int *)(this + 0xbc);
            local_14 = local_14 + 1) {
          *(double *)(*(int *)(*(int *)(this + 0xc4) + local_14 * 4) + (int)local_58 * 8) =
               *(double *)(*(int *)(*(int *)(this + 0xc4) + local_14 * 4) + (int)local_58 * 8) *
               (double)(&uStack_534)[(int)local_58];
        }
      }
      operator_delete(local_504);
    }
    local_8 = 0xffffffff;
    FUN_10013cdd((int)local_50);
    iVar2 = 1;
  }
  ExceptionList = local_10;
  return iVar2;
}

//===== 0x100316af =====

int __cdecl FUN_100316af(int param_1,int param_2)

{
  return *(int *)(param_1 + 4) - *(int *)(param_2 + 4);
}

//===== 0x100316c0 =====

undefined4 __cdecl FUN_100316c0(float *param_1,float *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x10031702 =====

/* public: void __thiscall Wvfm::sort(void) */

void __thiscall Wvfm::sort(Wvfm *this)

{
  int iVar1;
  void *pvVar2;
  int local_14;
  int local_10;
  int local_c;
  
                    /* 0x31702  404  ?sort@Wvfm@@QAEXXZ */
  if (*(int *)(this + 0xb4) < *(int *)(this + 0xb0)) {
    pvVar2 = operator_new(*(int *)(this + 0xb0) * 8 + 8);
    for (local_10 = 1; local_10 <= *(int *)(this + 0xb4); local_10 = local_10 + 1) {
      for (local_c = 1; local_c <= *(int *)(this + 0xb0); local_c = local_c + 1) {
        iVar1 = *(int *)(*(int *)(this + 0xc4) + local_c * 4);
        *(undefined4 *)((int)pvVar2 + local_c * 8) = *(undefined4 *)(iVar1 + local_10 * 8);
        *(undefined4 *)((int)pvVar2 + local_c * 8 + 4) = *(undefined4 *)(iVar1 + 4 + local_10 * 8);
      }
      qsort((void *)((int)pvVar2 + 8),*(size_t *)(this + 0xb0),8,FUN_10018750);
      for (local_c = 1; local_c <= *(int *)(this + 0xb0); local_c = local_c + 1) {
        iVar1 = *(int *)(*(int *)(this + 0xc4) + local_c * 4);
        *(undefined4 *)(iVar1 + local_10 * 8) = *(undefined4 *)((int)pvVar2 + local_c * 8);
        *(undefined4 *)(iVar1 + 4 + local_10 * 8) = *(undefined4 *)((int)pvVar2 + local_c * 8 + 4);
      }
    }
    operator_delete(pvVar2);
  }
  else {
    for (local_14 = 1; local_14 <= *(int *)(this + 0xb0); local_14 = local_14 + 1) {
      qsort((void *)(*(int *)(*(int *)(this + 0xc4) + local_14 * 4) + 8),*(size_t *)(this + 0xb4),8,
            FUN_10018750);
    }
  }
  return;
}

//===== 0x10031884 =====

/* public: double __thiscall Wvfm::sumEnvLite(class ShftVect const &,int,int)const  */

double __thiscall Wvfm::sumEnvLite(Wvfm *this,ShftVect *param_1,int param_2,int param_3)

{
  undefined4 uVar1;
  undefined4 uVar2;
  short sVar3;
  int iVar4;
  undefined4 local_1c;
  undefined4 uStack_18;
  int local_14;
  double local_10;
  int local_8;
  
                    /* 0x31884  420  ?sumEnvLite@Wvfm@@QBENABVShftVect@@HH@Z */
  local_10 = 0.0;
  sVar3 = ShftVect::maxshft(param_1);
  for (local_8 = param_2 + sVar3; local_8 <= param_3; local_8 = local_8 + 1) {
    sVar3 = ShftVect::s(param_1,1);
    iVar4 = *(int *)(*(int *)(this + 0xc4) + (local_8 - sVar3) * 4);
    local_1c = *(undefined4 *)(iVar4 + 8);
    uStack_18 = *(undefined4 *)(iVar4 + 0xc);
    local_14 = 2;
    while( true ) {
      iVar4 = cols(this);
      if (iVar4 < local_14) break;
      sVar3 = ShftVect::s(param_1,local_14);
      iVar4 = *(int *)(*(int *)(this + 0xc4) + (local_8 - sVar3) * 4);
      uVar1 = *(undefined4 *)(iVar4 + local_14 * 8);
      uVar2 = *(undefined4 *)(iVar4 + 4 + local_14 * 8);
      if ((double)CONCAT44(uStack_18,local_1c) < (double)CONCAT44(uVar2,uVar1)) {
        local_1c = uVar1;
        uStack_18 = uVar2;
      }
      local_14 = local_14 + 1;
    }
    local_10 = local_10 + (double)CONCAT44(uStack_18,local_1c);
  }
  return local_10;
}

//===== 0x10031976 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: void __thiscall Wvfm::envelope(class ShftVect const &)const  */

void __thiscall Wvfm::envelope(Wvfm *this,ShftVect *param_1)

{
  double dVar1;
  int iVar2;
  short sVar3;
  double *pdVar4;
  int *piVar5;
  float *pfVar6;
  double dVar7;
  float local_5c;
  double local_54;
  undefined1 local_4c [8];
  float local_44;
  undefined4 local_40;
  float local_3c;
  undefined4 local_38;
  float local_34;
  undefined4 local_30;
  float local_2c;
  undefined4 local_28;
  undefined8 local_24;
  long local_1c;
  Wvfm *local_18;
  int local_14;
  int local_10;
  int local_c;
  undefined4 local_8;
  
  local_18 = this;
                    /* 0x31976  151  ?envelope@Wvfm@@QBEXABVShftVect@@@Z */
  sVar3 = ShftVect::maxshft(param_1);
  local_10 = sVar3 + 1;
  local_1c = rows(this);
  local_14 = cols(this);
  if (*(int *)(this + 200) == 0) {
    pdVar4 = dvector(1,local_1c);
    *(double **)(local_18 + 200) = pdVar4;
  }
  if (*(int *)(this + 0xcc) == 0) {
    piVar5 = ivector(1,local_1c);
    *(int **)(local_18 + 0xcc) = piVar5;
  }
  if (*(int *)(this + 0xd0) == 0) {
    pdVar4 = dvector(1,local_1c);
    *(double **)(local_18 + 0xd0) = pdVar4;
  }
  if (*(int *)(this + 0xd4) == 0) {
    pfVar6 = vector(1,local_1c);
    *(float **)(local_18 + 0xd4) = pfVar6;
  }
  if ((((*(int *)(this + 200) == 0) || (*(int *)(this + 0xcc) == 0)) || (*(int *)(this + 0xd0) == 0)
      ) || (*(int *)(this + 0xd4) == 0)) {
    *(undefined4 *)(local_18 + 0x168) = 2;
  }
  else {
    for (local_c = 1; local_c < local_10; local_c = local_c + 1) {
      iVar2 = *(int *)(local_18 + 200);
      *(undefined4 *)(iVar2 + local_c * 8) = 0;
      *(undefined4 *)(iVar2 + 4 + local_c * 8) = 0;
      iVar2 = *(int *)(local_18 + 0xd0);
      *(undefined4 *)(iVar2 + local_c * 8) = 0;
      *(undefined4 *)(iVar2 + 4 + local_c * 8) = 0;
      *(undefined4 *)(*(int *)(local_18 + 0xd4) + local_c * 4) = 0;
      *(undefined4 *)(*(int *)(local_18 + 0xcc) + local_c * 4) = 0;
    }
    for (local_c = local_10; local_c <= local_1c; local_c = local_c + 1) {
      local_40 = 1;
      sVar3 = ShftVect::s(param_1,1);
      local_44 = (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + (local_c - sVar3) * 4) + 8);
      local_38 = 2;
      sVar3 = ShftVect::s(param_1,2);
      local_3c = (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + (local_c - sVar3) * 4) + 0x10);
      local_30 = 3;
      sVar3 = ShftVect::s(param_1,3);
      local_34 = (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + (local_c - sVar3) * 4) + 0x18);
      local_28 = 4;
      sVar3 = ShftVect::s(param_1,4);
      local_2c = (float)*(double *)(*(int *)(*(int *)(this + 0xc4) + (local_c - sVar3) * 4) + 0x20);
      if (local_3c < local_44) {
        FUN_10031def((int)local_4c,1,2);
      }
      if (local_34 < local_3c) {
        FUN_10031def((int)local_4c,2,3);
      }
      if (local_2c < local_34) {
        FUN_10031def((int)local_4c,3,4);
      }
      if (local_3c < local_44) {
        FUN_10031def((int)local_4c,1,2);
      }
      if (local_34 < local_3c) {
        FUN_10031def((int)local_4c,2,3);
      }
      if (local_3c < local_44) {
        FUN_10031def((int)local_4c,1,2);
      }
      dVar7 = (double)local_2c;
      local_54 = (double)local_34;
      local_8 = local_28;
      if (local_44 < (float)_DAT_10038e80) {
        local_44 = 0.0;
      }
      if (local_34 < (float)_DAT_10038e80) {
        local_34 = 0.0;
      }
      if (local_2c == local_34) {
        local_5c = 0.5;
      }
      else {
        local_5c = (local_34 - local_44) / (local_2c - local_34);
      }
      *(float *)(*(int *)(local_18 + 0xd4) + local_c * 4) = local_5c;
      if (_DAT_10038ea0 < *(float *)(*(int *)(local_18 + 0xd4) + local_c * 4)) {
        *(undefined4 *)(*(int *)(local_18 + 0xd4) + local_c * 4) = 0x411fd70a;
      }
      iVar2 = *(int *)(local_18 + 200);
      local_24._0_4_ = SUB84(dVar7,0);
      *(undefined4 *)(iVar2 + local_c * 8) = (undefined4)local_24;
      local_24._4_4_ = (undefined4)((ulonglong)dVar7 >> 0x20);
      *(undefined4 *)(iVar2 + 4 + local_c * 8) = local_24._4_4_;
      *(undefined4 *)(*(int *)(local_18 + 0xcc) + local_c * 4) = local_28;
      if (local_54 < _DAT_10038ea8) {
        local_54 = 2.220446049250313e-16;
      }
      if (_DAT_10038eb0 <= dVar7) {
        local_24 = dVar7 / local_54;
      }
      else {
        dVar1 = (double)_DAT_10038e58;
        local_24 = dVar7;
        dVar7 = sqrt(local_54);
        local_24 = local_24 / dVar7 + dVar1;
      }
      if ((float)local_24 <= _DAT_10038e54) {
        if ((float)local_24 < _DAT_10038e58) {
          local_24 = (double)_DAT_10038e58;
        }
      }
      else {
        local_24 = (double)_DAT_10038e54;
      }
      iVar2 = *(int *)(local_18 + 0xd0);
      *(undefined4 *)(iVar2 + local_c * 8) = (undefined4)local_24;
      *(undefined4 *)(iVar2 + 4 + local_c * 8) = local_24._4_4_;
    }
  }
  return;
}

//===== 0x10031def =====

void __cdecl FUN_10031def(int param_1,int param_2,int param_3)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  
  uVar1 = *(undefined4 *)(param_1 + param_2 * 8);
  uVar2 = *(undefined4 *)(param_1 + 4 + param_2 * 8);
  uVar3 = *(undefined4 *)(param_1 + 4 + param_3 * 8);
  *(undefined4 *)(param_1 + param_2 * 8) = *(undefined4 *)(param_1 + param_3 * 8);
  *(undefined4 *)(param_1 + 4 + param_2 * 8) = uVar3;
  *(undefined4 *)(param_1 + param_3 * 8) = uVar1;
  *(undefined4 *)(param_1 + 4 + param_3 * 8) = uVar2;
  return;
}

//===== 0x10031e3b =====

/* public: void __thiscall Wvfm::append(class Wvfm const &,int,int) */

void __thiscall Wvfm::append(Wvfm *this,Wvfm *param_1,int param_2,int param_3)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  int local_348;
  int local_340;
  int local_33c;
  int local_334;
  ShftVect local_32c [8];
  int local_324;
  undefined4 local_320;
  Wvfm local_31c [176];
  undefined4 local_26c;
  undefined4 local_268;
  undefined4 local_264;
  undefined4 local_260;
  int local_258;
  int local_1c;
  undefined4 local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
                    /* 0x31e3b  72  ?append@Wvfm@@QAEXABV1@HH@Z */
  local_8 = 0xffffffff;
  puStack_c = &LAB_10037581;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  iVar3 = endi(param_1);
  iVar4 = rows(param_1);
  if (iVar3 < iVar4) {
    local_348 = endi(param_1);
  }
  else {
    local_348 = rows(param_1);
  }
  Wvfm(local_31c,param_2 + 1 + (local_348 - param_3),4,(char *)(this + 0xdc),2,0);
  local_8 = 0;
  ShftVect::ShftVect(local_32c);
  local_14 = *(undefined4 *)(this + 0xb0);
  local_320 = *(undefined4 *)(this + 0xb4);
  local_324 = local_1c;
  for (local_334 = 1; local_334 < 5; local_334 = local_334 + 1) {
    for (local_340 = 1; local_340 <= param_2; local_340 = local_340 + 1) {
      iVar3 = *(int *)(*(int *)(this + 0xc4) + local_340 * 4);
      iVar4 = *(int *)(local_258 + local_340 * 4);
      *(undefined4 *)(iVar4 + local_334 * 8) = *(undefined4 *)(iVar3 + local_334 * 8);
      *(undefined4 *)(iVar4 + 4 + local_334 * 8) = *(undefined4 *)(iVar3 + 4 + local_334 * 8);
      *(undefined4 *)(local_1c + local_340 * 4) =
           *(undefined4 *)(*(int *)(this + 0x300) + local_340 * 4);
    }
    for (local_33c = param_3; local_33c <= local_348; local_33c = local_33c + 1) {
      iVar3 = *(int *)(*(int *)(param_1 + 0xc4) + local_33c * 4);
      iVar4 = *(int *)(local_258 + local_340 * 4);
      *(undefined4 *)(iVar4 + local_334 * 8) = *(undefined4 *)(iVar3 + local_334 * 8);
      *(undefined4 *)(iVar4 + 4 + local_334 * 8) = *(undefined4 *)(iVar3 + 4 + local_334 * 8);
      *(undefined4 *)(local_1c + local_340 * 4) =
           *(undefined4 *)(*(int *)(param_1 + 0x300) + local_33c * 4);
      local_340 = local_340 + 1;
    }
  }
  *(undefined4 *)(this + 0xb0) = local_26c;
  *(undefined4 *)(this + 0xb4) = local_268;
  uVar1 = *(undefined4 *)(this + 0xc4);
  uVar2 = *(undefined4 *)(this + 0x300);
  *(int *)(this + 0xc4) = local_258;
  *(int *)(this + 0x300) = local_1c;
  *(undefined4 *)(this + 0xb8) = local_264;
  *(undefined4 *)(this + 0xbc) = local_260;
  local_26c = local_14;
  local_268 = local_320;
  local_258 = uVar1;
  local_1c = uVar2;
  iVar3 = rows(this);
  if (*(int *)(this + 200) != 0) {
    free_dvector(*(double **)(this + 200),1,iVar3);
    *(undefined4 *)(this + 200) = 0;
  }
  if (*(int *)(this + 0xcc) != 0) {
    free_ivector(*(int **)(this + 0xcc),1,iVar3);
    *(undefined4 *)(this + 0xcc) = 0;
  }
  if (*(int *)(this + 0xd0) != 0) {
    free_dvector(*(double **)(this + 0xd0),1,iVar3);
    *(undefined4 *)(this + 0xd0) = 0;
  }
  if (*(int *)(this + 0xd4) != 0) {
    free_vector(*(float **)(this + 0xd4),1,iVar3);
    *(undefined4 *)(this + 0xd4) = 0;
  }
  envelope(this,local_32c);
  local_8 = 0xffffffff;
  ~Wvfm(local_31c);
  ExceptionList = local_10;
  return;
}

//===== 0x1003223e =====

/* public: void __thiscall Wvfm::lnordr(char const *) */

void __thiscall Wvfm::lnordr(Wvfm *this,char *param_1)

{
  int iVar1;
  int local_8;
  
                    /* 0x3223e  266  ?lnordr@Wvfm@@QAEXPBD@Z */
  for (local_8 = 0; local_8 < 6; local_8 = local_8 + 1) {
    iVar1 = toupper((int)param_1[local_8]);
    this[local_8 + 0xdc] = SUB41(iVar1,0);
  }
  return;
}

//===== 0x10032286 =====

/* public: void __thiscall Wvfm::ssm(double const *,int) */

void __thiscall Wvfm::ssm(Wvfm *this,double *param_1,int param_2)

{
  int iVar1;
  int local_c;
  int local_8;
  
                    /* 0x32286  411  ?ssm@Wvfm@@QAEXPBNH@Z */
  this[0x170] = param_2._0_1_;
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    for (local_c = 0; local_c < 4; local_c = local_c + 1) {
      iVar1 = local_c + local_8 * 4;
      *(undefined4 *)(this + local_c * 8 + local_8 * 0x20 + 0xe8) = *(undefined4 *)(param_1 + iVar1)
      ;
      *(undefined4 *)(this + local_c * 8 + local_8 * 0x20 + 0xec) =
           *(undefined4 *)((int)param_1 + iVar1 * 8 + 4);
    }
  }
  return;
}

//===== 0x10032306 =====

/* private: void __thiscall Wvfm::pm(double * *,float *,int,int,int) */

void __thiscall
Wvfm::pm(Wvfm *this,double **param_1,float *param_2,int param_3,int param_4,int param_5)

{
  int local_c;
  
                    /* 0x32306  301  ?pm@Wvfm@@AAEXPAPANPAMHHH@Z */
  release(this);
  *(double ***)(this + 0xc4) = param_1;
  *(float **)(this + 0x300) = param_2;
  *(int *)(this + 0xb0) = param_3;
  *(int *)(this + 0xb8) = param_4;
  if (*(int *)(this + 0xb0) < param_5) {
    local_c = *(int *)(this + 0xb0);
  }
  else {
    local_c = param_5;
  }
  *(int *)(this + 0xbc) = local_c;
  return;
}

//===== 0x1003237b =====

/* public: void __thiscall Wvfm::setMCoef(int,int,float,float,float) */

void __thiscall
Wvfm::setMCoef(Wvfm *this,int param_1,int param_2,float param_3,float param_4,float param_5)

{
                    /* 0x3237b  368  ?setMCoef@Wvfm@@QAEXHHMMM@Z */
  *(int *)(this + 0x17c) = param_2;
  *(float *)(this + param_1 * 0xc + 0x180) = param_3;
  *(float *)(this + param_1 * 0xc + 0x184) = param_4;
  *(float *)(this + param_1 * 0xc + 0x188) = param_5;
  return;
}

//===== 0x100323cd =====

/* WARNING: Type propagation algorithm not settling */
/* public: void __thiscall Wvfm::majorMinorCode(enum Wvfm::StsMajor &,int &,char const * *)const  */

void __thiscall Wvfm::majorMinorCode(Wvfm *this,StsMajor *param_1,int *param_2,char **param_3)

{
  StsMajor local_188 [2];
  char *local_180 [94];
  uint local_8;
  
                    /* 0x323cd  273  ?majorMinorCode@Wvfm@@QBEXAAW4StsMajor@1@AAHPAPBD@Z */
  local_188[0] = 1;
  local_188[1] = 0;
  local_180[0] = (char *)0x0;
  local_180[1] = s_No_problem_s__10040f24;
  local_180[2] = (char *)0x0;
  local_180[3] = (char *)0x1;
  local_180[4] = (char *)0x0;
  local_180[5] = s_Class_Wvfm_uninitialized_10040f34;
  local_180[6] = (char *)0x2;
  local_180[7] = (char *)0x2;
  local_180[8] = (char *)0x0;
  local_180[9] = s_Insufficient_memory_10040f50;
  local_180[10] = (char *)0xa;
  local_180[0xb] = (char *)0x3;
  local_180[0xc] = (char *)0x0;
  local_180[0xd] = s_No_peaks_found_during_sample_rat_10040f64;
  local_180[0xe] = (char *)0xb;
  local_180[0xf] = (char *)0x3;
  local_180[0x10] = (char *)0x1;
  local_180[0x11] = s_Start_Stop_point_detection_incon_10040f98;
  local_180[0x12] = (char *)0x7;
  local_180[0x13] = (char *)0x3;
  local_180[0x14] = (char *)0x2;
  local_180[0x15] = s_Class_Wvfm_is_corrupt_10040fc0;
  local_180[0x16] = (char *)0xc;
  local_180[0x17] = (char *)0x4;
  local_180[0x18] = (char *)0x0;
  local_180[0x19] = s_Failed_to_derive_spec_separation_10040fd8;
  local_180[0x1a] = (char *)0xd;
  local_180[0x1b] = (char *)0x4;
  local_180[0x1c] = (char *)0x1;
  local_180[0x1d] = s_Too_few_peaks_to_derive_spec_sep_10041000;
  local_180[0x1e] = (char *)0xe;
  local_180[0x1f] = (char *)0x4;
  local_180[0x20] = (char *)0x2;
  local_180[0x21] = s_Singular_cross_talk_matrix_deriv_10041030;
  local_180[0x22] = (char *)0xf;
  local_180[0x23] = (char *)0x4;
  local_180[0x24] = (char *)0x3;
  local_180[0x25] = s_Angle_Algorithm_and_error_code_n_10041054;
  local_180[0x26] = (char *)0x10;
  local_180[0x27] = (char *)0x4;
  local_180[0x28] = (char *)0x4;
  local_180[0x29] = s_Angle_Algorithm_and_error_code_n_10041084;
  local_180[0x2a] = (char *)0x11;
  local_180[0x2b] = (char *)0x4;
  local_180[0x2c] = (char *)0x5;
  local_180[0x2d] = s_Spec_separation_matrix_has_a_dia_100410b4;
  local_180[0x2e] = (char *)0x12;
  local_180[0x2f] = (char *)0x4;
  local_180[0x30] = (char *)0x6;
  local_180[0x31] = s_Cross_talk_clue_found_lacking_100410ec;
  local_180[0x32] = (char *)0x13;
  local_180[0x33] = (char *)0x4;
  local_180[0x34] = (char *)0x7;
  local_180[0x35] = s_Spec_separation_qc_value_exceeds_1004110c;
  local_180[0x36] = (char *)0x15;
  local_180[0x37] = (char *)0x5;
  local_180[0x38] = (char *)0x0;
  local_180[0x39] = s_Failed_1st_read_of_1st_segment_10041134;
  local_180[0x3a] = (char *)0x16;
  local_180[0x3b] = (char *)0x5;
  local_180[0x3c] = (char *)0x1;
  local_180[0x3d] = s_Failed_2nd_read_of_1st_segment_10041154;
  local_180[0x3e] = (char *)0x17;
  local_180[0x3f] = (char *)0x5;
  local_180[0x40] = (char *)0x2;
  local_180[0x41] = s_Failed_1st_segment_Output_add___10041174;
  local_180[0x42] = (char *)0x14;
  local_180[0x43] = (char *)0x6;
  local_180[0x44] = (char *)0x0;
  local_180[0x45] = s_No_license_or_license_expired_10041194;
  local_180[0x46] = (char *)0x3;
  local_180[0x47] = (char *)0x7;
  local_180[0x48] = (char *)0x0;
  local_180[0x49] = s_Archaic_class_access__circa_1996_10040f00;
  local_180[0x4a] = (char *)0x4;
  local_180[0x4b] = (char *)0x7;
  local_180[0x4c] = (char *)0x1;
  local_180[0x4d] = s_Archaic_class_access__circa_1996_10040f00;
  local_180[0x4e] = (char *)0x5;
  local_180[0x4f] = (char *)0x7;
  local_180[0x50] = (char *)0x2;
  local_180[0x51] = s_Archaic_class_access__circa_1996_10040f00;
  local_180[0x52] = (char *)0x6;
  local_180[0x53] = (char *)0x7;
  local_180[0x54] = (char *)0x3;
  local_180[0x55] = s_Archaic_class_access__circa_1996_10040f00;
  local_180[0x56] = (char *)0x8;
  local_180[0x57] = (char *)0x7;
  local_180[0x58] = (char *)0x4;
  local_180[0x59] = s_Archaic_class_access__circa_1996_10040f00;
  local_180[0x5a] = (char *)0x9;
  local_180[0x5b] = (char *)0x7;
  local_180[0x5c] = (char *)0x5;
  local_180[0x5d] = s_Archaic_class_access__circa_1996_10040f00;
  *param_1 = 0xffffffff;
  *param_2 = -1;
  *param_3 = s_Unknown_class_status_100411b4;
  local_8 = 0;
  while( true ) {
    if (0x17 < local_8) {
      return;
    }
    if (*(StsMajor *)(this + 0x168) == local_188[local_8 * 4]) break;
    local_8 = local_8 + 1;
  }
  *param_1 = local_188[local_8 * 4 + 1];
  *param_2 = (int)local_180[local_8 * 4];
  *param_3 = local_180[local_8 * 4 + 1];
  return;
}

//===== 0x100327e3 =====

/* public: void __thiscall Wvfm::debug(char const *)const  */

void __thiscall Wvfm::debug(Wvfm *this,char *param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int local_10;
  int local_c;
  int local_8;
  
                    /* 0x327e3  133  ?debug@Wvfm@@QBEXPBD@Z */
  printf(s_Wvfm____p_10041258);
  if (param_1 != (char *)0x0) {
    printf(s__s_10041264);
  }
  method(this);
  printf(s_rows__u_cols__u_bgni__u_endi__u_m_1004126c);
  printf(s_datasrc____s__10041298);
  printf(s_lnordr____s__100412a8);
  ObsInpSpec::debug((ObsInpSpec *)(this + 0x210));
  if ((((*(int *)(this + 0xc0) == 1) || (*(int *)(this + 0xc0) == 2)) ||
      (*(int *)(this + 0xc0) == 4)) ||
     (((*(int *)(this + 0xc0) == 5 || (*(int *)(this + 0xc0) == 6)) || (*(int *)(this + 0xc0) == 7))
     )) {
    printf(s_specsep__Calculated___s_100412c0);
    for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
      printf(&DAT_100412dc);
      for (local_c = 0; local_c < 4; local_c = local_c + 1) {
        printf(s__9_6f_100412e0,*(undefined4 *)(this + local_c * 8 + local_8 * 0x20 + 0xe8));
      }
      printf(&DAT_100412e8);
    }
  }
  printf(s_MCoef__100412ec);
  printf(s_smpls__3d_100412f4);
  printf(s__7_4f__7_4f__11_8f_10041304,(double)*(float *)(this + 0x180),
         (double)*(float *)(this + 0x184),(double)*(float *)(this + 0x188));
  printf(s__7_4f__7_4f__11_8f_1004131c,(double)*(float *)(this + 0x18c),
         (double)*(float *)(this + 400),(double)*(float *)(this + 0x194));
  printf(s__7_4f__7_4f__11_8f_10041334,(double)*(float *)(this + 0x198),
         (double)*(float *)(this + 0x19c),(double)*(float *)(this + 0x1a0));
  printf(s__7_4f__7_4f__11_8f_1004134c,(double)*(float *)(this + 0x1a4),
         (double)*(float *)(this + 0x1a8),(double)*(float *)(this + 0x1ac));
  if (*(int *)(this + 0xc4) == 0) {
    printf(s_pm____null__10041364);
  }
  else {
    printf(s_pm____p_10041374);
    if (*(int *)(this + 0xb4) < *(int *)(this + 0xb0)) {
      for (local_10 = *(int *)(this + 0xb8); local_10 <= *(int *)(this + 0xbc);
          local_10 = local_10 + 1) {
        iVar1 = *(int *)(*(int *)(this + 0xc4) + local_10 * 4);
        iVar2 = *(int *)(*(int *)(this + 0xc4) + local_10 * 4);
        iVar3 = *(int *)(*(int *)(this + 0xc4) + local_10 * 4);
        iVar4 = *(int *)(*(int *)(this + 0xc4) + local_10 * 4);
        printf(s__4ld__6_2lf__6_2lf__6_2lf__6_2lf_10041380,local_10,*(undefined4 *)(iVar4 + 8),
               *(undefined4 *)(iVar4 + 0xc),*(undefined4 *)(iVar3 + 0x10),
               *(undefined4 *)(iVar3 + 0x14),*(undefined4 *)(iVar2 + 0x18),
               *(undefined4 *)(iVar2 + 0x1c),*(undefined4 *)(iVar1 + 0x20),
               *(undefined4 *)(iVar1 + 0x24),
               (double)*(float *)(*(int *)(this + 0x300) + local_10 * 4));
      }
    }
    else {
      for (local_10 = *(int *)(this + 0xb8); local_10 <= *(int *)(this + 0xbc);
          local_10 = local_10 + 1) {
        printf(s__4ld__6_2lf__6_2lf__6_2lf__6_2lf_100413a8,local_10,
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 4) + local_10 * 8),
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 4) + 4 + local_10 * 8),
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 8) + local_10 * 8),
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 8) + 4 + local_10 * 8),
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 0xc) + local_10 * 8),
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 0xc) + 4 + local_10 * 8),
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 0x10) + local_10 * 8),
               *(undefined4 *)(*(int *)(*(int *)(this + 0xc4) + 0x10) + 4 + local_10 * 8),
               (double)*(float *)(*(int *)(this + 0x300) + local_10 * 4));
      }
    }
  }
  return;
}

//===== 0x10032c86 =====

/* private: char const * __thiscall Wvfm::errmsg(void)const  */

char * __thiscall Wvfm::errmsg(Wvfm *this)

{
  uint local_c;
  
                    /* 0x32c86  154  ?errmsg@Wvfm@@ABEPBDXZ */
  local_c = 0;
  while( true ) {
    if (0x14 < local_c) {
      return s_STS_UNKNOWN__1004152c;
    }
    if (*(int *)(this + 0x168) == *(int *)(&DAT_10038eb8 + local_c * 8)) break;
    local_c = local_c + 1;
  }
  return (&PTR_s_STS_UNINITD_10038ebc)[local_c * 2];
}

//===== 0x10032cdb =====

/* public: void __thiscall Wvfm::setSSTPattern(struct SSTLUT const * const) */

void __thiscall Wvfm::setSSTPattern(Wvfm *this,SSTLUT *param_1)

{
  int iVar1;
  SSTLUT *pSVar2;
  Wvfm *pWVar3;
  int local_8;
  
                    /* 0x32cdb  375  ?setSSTPattern@Wvfm@@QAEXQBUSSTLUT@@@Z */
  *(undefined4 *)(this + 0x1bc) = 1;
  for (local_8 = 0; local_8 < 4; local_8 = local_8 + 1) {
    pSVar2 = param_1 + local_8 * 0x14;
    pWVar3 = this + local_8 * 0x14 + 0x1c0;
    for (iVar1 = 5; iVar1 != 0; iVar1 = iVar1 + -1) {
      *(undefined4 *)pWVar3 = *(undefined4 *)pSVar2;
      pSVar2 = pSVar2 + 4;
      pWVar3 = pWVar3 + 4;
    }
  }
  return;
}

//===== 0x10032d40 =====

float10 __thiscall FUN_10032d40(int param_1,int param_2,int param_3)

{
  return (float10)*(float *)(param_1 + (param_2 + -1) * 0x10 + 0x38c + param_3 * 4);
}

//===== 0x10032d70 =====

int __thiscall FUN_10032d70(void *this,int param_1)

{
  return (int)this + param_1 * 0x14 + 0x3e0;
}

//===== 0x10032d90 =====

undefined4 __fastcall FUN_10032d90(int param_1)

{
  return *(undefined4 *)(param_1 + 0x430);
}

//===== 0x10032db0 =====

undefined4 __thiscall FUN_10032db0(void *this,int param_1)

{
  return *(undefined4 *)((int)this + param_1 * 4 + 0x434);
}

//===== 0x10032dd0 =====

undefined4 __thiscall FUN_10032dd0(void *this,int param_1)

{
  return *(undefined4 *)((int)this + param_1 * 4 + 0x444);
}

//===== 0x10032df0 =====

undefined4 __fastcall FUN_10032df0(int param_1)

{
  return *(undefined4 *)(param_1 + 0x454);
}

//===== 0x10032e10 =====

/* private: double * __thiscall Wvfm::dmscanlprod(void)const  */

double * __thiscall Wvfm::dmscanlprod(Wvfm *this)

{
  int iVar1;
  double *pdVar2;
  int local_10;
  int local_c;
  
                    /* 0x32e10  140  ?dmscanlprod@Wvfm@@ABEPANXZ */
  iVar1 = rows(this);
  pdVar2 = dvector(1,iVar1);
  if (pdVar2 != (double *)0x0) {
    local_c = 1;
    while( true ) {
      iVar1 = rows(this);
      if (iVar1 < local_c) break;
      iVar1 = *(int *)(*(int *)(this + 0xc4) + local_c * 4);
      *(undefined4 *)(pdVar2 + local_c) = *(undefined4 *)(iVar1 + 8);
      *(undefined4 *)((int)pdVar2 + local_c * 8 + 4) = *(undefined4 *)(iVar1 + 0xc);
      local_10 = 2;
      while( true ) {
        iVar1 = cols(this);
        if (iVar1 < local_10) break;
        pdVar2[local_c] =
             pdVar2[local_c] *
             *(double *)(*(int *)(*(int *)(this + 0xc4) + local_c * 4) + local_10 * 8);
        local_10 = local_10 + 1;
      }
      local_c = local_c + 1;
    }
  }
  return pdVar2;
}

//===== 0x10032ed0 =====

/* private: double * __thiscall Wvfm::dmscanlsum(void)const  */

double * __thiscall Wvfm::dmscanlsum(Wvfm *this)

{
  int iVar1;
  double *pdVar2;
  int local_10;
  int local_c;
  
                    /* 0x32ed0  141  ?dmscanlsum@Wvfm@@ABEPANXZ */
  iVar1 = rows(this);
  pdVar2 = dvector(1,iVar1);
  if (pdVar2 != (double *)0x0) {
    local_c = 1;
    while( true ) {
      iVar1 = rows(this);
      if (iVar1 < local_c) break;
      iVar1 = *(int *)(*(int *)(this + 0xc4) + local_c * 4);
      *(undefined4 *)(pdVar2 + local_c) = *(undefined4 *)(iVar1 + 8);
      *(undefined4 *)((int)pdVar2 + local_c * 8 + 4) = *(undefined4 *)(iVar1 + 0xc);
      local_10 = 2;
      while( true ) {
        iVar1 = cols(this);
        if (iVar1 < local_10) break;
        pdVar2[local_c] =
             pdVar2[local_c] +
             *(double *)(*(int *)(*(int *)(this + 0xc4) + local_c * 4) + local_10 * 8);
        local_10 = local_10 + 1;
      }
      local_c = local_c + 1;
    }
  }
  return pdVar2;
}

//===== 0x10032f90 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* public: int __thiscall Wvfm::unstop(void) */

int __thiscall Wvfm::unstop(Wvfm *this)

{
  int iVar1;
  int iVar2;
  double *pdVar3;
  double *pdVar4;
  int local_6c;
  int local_68;
  double local_58;
  undefined4 local_50;
  undefined4 uStack_4c;
  undefined4 local_48;
  undefined4 uStack_44;
  int local_40;
  int local_3c;
  double local_38;
  int local_30;
  double *local_2c;
  double local_28;
  double local_20;
  double local_18;
  int local_10;
  double *local_c;
  int local_8;
  
                    /* 0x32f90  428  ?unstop@Wvfm@@QAEHXZ */
  local_8 = 1;
  while( true ) {
    if (local_8 != 1) {
      return 1;
    }
    local_8 = 0;
    local_c = dmscanlprod(this);
    if (local_c == (double *)0x0) {
      return 0;
    }
    local_2c = dmscanlsum(this);
    if (local_2c == (double *)0x0) {
      return 0;
    }
    pdVar4 = &local_38;
    pdVar3 = &local_18;
    iVar1 = rows(this);
    FUN_10033269((int)local_c,iVar1,pdVar3,pdVar4);
    pdVar4 = &local_58;
    pdVar3 = &local_20;
    iVar1 = rows(this);
    FUN_10033269((int)local_2c,iVar1,pdVar3,pdVar4);
    local_48 = *(undefined4 *)(local_c + 1);
    uStack_44 = *(undefined4 *)((int)local_c + 0xc);
    local_3c = 1;
    local_50 = *(undefined4 *)(local_2c + 1);
    uStack_4c = *(undefined4 *)((int)local_2c + 0xc);
    local_40 = 1;
    if ((_DAT_10038f60 == local_38) || (_DAT_10038f60 == local_58)) break;
    local_30 = 1;
    while (iVar1 = rows(this), local_30 <= iVar1) {
      local_c[local_30] = (local_c[local_30] - local_18) / local_38;
      local_2c[local_30] = (local_2c[local_30] - local_20) / local_58;
      if ((double)CONCAT44(uStack_44,local_48) < local_c[local_30]) {
        local_48 = *(undefined4 *)(local_c + local_30);
        uStack_44 = *(undefined4 *)((int)local_c + local_30 * 8 + 4);
        local_3c = local_30;
      }
      if ((double)CONCAT44(uStack_4c,local_50) < local_2c[local_30]) {
        local_50 = *(undefined4 *)(local_2c + local_30);
        uStack_4c = *(undefined4 *)((int)local_2c + local_30 * 8 + 4);
        local_40 = local_30;
      }
      local_30 = local_30 + 1;
    }
    iVar1 = rows(this);
    free_dvector(local_c,1,iVar1);
    iVar1 = rows(this);
    free_dvector(local_2c,1,iVar1);
    iVar1 = abs(local_3c - local_40);
    if ((iVar1 < 10) &&
       (local_28 = sqrt((double)CONCAT44(uStack_44,local_48) * (double)CONCAT44(uStack_4c,local_50))
       , _DAT_10038f68 < local_28)) {
      local_8 = 1;
      if (local_40 < 0x1a) {
        local_68 = 1;
      }
      else {
        local_68 = local_40 + -0x19;
      }
      iVar2 = local_40 + 0x19;
      iVar1 = rows(this);
      if (iVar2 < iVar1) {
        local_6c = local_40 + 0x19;
      }
      else {
        local_6c = rows(this);
      }
      for (local_10 = 1; local_10 < 5; local_10 = local_10 + 1) {
        for (local_30 = local_68; local_30 <= local_6c; local_30 = local_30 + 1) {
          sc_la_set(this,local_30,local_10,0.0);
        }
      }
    }
  }
  iVar1 = rows(this);
  free_dvector(local_c,1,iVar1);
  iVar1 = rows(this);
  free_dvector(local_2c,1,iVar1);
  return 0;
}

//===== 0x10033269 =====

void __cdecl FUN_10033269(int param_1,int param_2,double *param_3,double *param_4)

{
  double dVar1;
  undefined4 local_8;
  
  *(undefined4 *)param_4 = 0;
  *(undefined4 *)((int)param_4 + 4) = 0;
  *(undefined4 *)param_3 = 0;
  *(undefined4 *)((int)param_3 + 4) = 0;
  for (local_8 = 1; local_8 <= param_2; local_8 = local_8 + 1) {
    *param_3 = *param_3 + *(double *)(param_1 + local_8 * 8);
  }
  *param_3 = *param_3 / (double)param_2;
  for (local_8 = 1; local_8 <= param_2; local_8 = local_8 + 1) {
    dVar1 = *(double *)(param_1 + local_8 * 8) - *param_3;
    *param_4 = dVar1 * dVar1 + *param_4;
  }
  dVar1 = sqrt(*param_4 / (double)param_2);
  *param_4 = dVar1;
  return;
}

//===== 0x10033324 =====

/* WARNING: Type propagation algorithm not settling */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __thiscall
FUN_10033324(void *this,Wvfm *param_1,Wvfm *param_2,int param_3,uint param_4,uint *param_5)

{
  undefined4 uVar1;
  short sVar2;
  int iVar3;
  undefined4 *puVar4;
  double dVar5;
  undefined4 local_e4;
  Wvfm *local_c0;
  Wvfm *local_bc;
  undefined4 local_a4 [2];
  Wvfm *local_9c;
  Wvfm *local_98;
  Wvfm *local_94;
  Wvfm *local_90;
  Wvfm *local_8c;
  Wvfm *local_88;
  Wvfm *local_84;
  Wvfm *local_80;
  Wvfm *local_7c;
  Wvfm *local_78;
  Wvfm *local_74;
  Wvfm *local_70;
  int local_6c;
  int local_68;
  undefined4 local_64;
  undefined4 local_60;
  Wvfm *local_5c;
  Wvfm *local_58;
  undefined8 local_54;
  undefined4 local_4c [8];
  Wvfm *local_2c;
  Wvfm *local_28;
  int local_24;
  undefined4 local_20;
  undefined4 local_1c;
  ShftVect *local_18;
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_100375a6;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  local_18 = (ShftVect *)FUN_100241e0((int)this);
  local_20 = 0;
  local_1c = 0;
  if ((param_4 & 1) != 0) {
    local_70 = operator_new(0x308);
    local_8 = 0;
    if (local_70 == (Wvfm *)0x0) {
      local_bc = (Wvfm *)0x0;
    }
    else {
      local_bc = (Wvfm *)Wvfm::Wvfm(local_70,param_2);
    }
    local_74 = local_bc;
    local_8 = 0xffffffff;
    local_58 = local_bc;
    local_78 = operator_new(0x308);
    local_8 = 1;
    if (local_78 == (Wvfm *)0x0) {
      local_c0 = (Wvfm *)0x0;
    }
    else {
      local_c0 = (Wvfm *)Wvfm::Wvfm(local_78,param_1);
    }
    local_7c = local_c0;
    local_8 = 0xffffffff;
    local_28 = local_c0;
    if ((local_58 == (Wvfm *)0x0) || (local_c0 == (Wvfm *)0x0)) {
      if (local_58 != (Wvfm *)0x0) {
        local_84 = local_58;
        local_80 = local_58;
        if (local_58 != (Wvfm *)0x0) {
          FUN_10019250(local_58,1);
        }
      }
      if (local_28 != (Wvfm *)0x0) {
        local_8c = local_28;
        local_88 = local_28;
        if (local_28 != (Wvfm *)0x0) {
          FUN_10019250(local_28,1);
        }
      }
      ExceptionList = local_10;
      return 0;
    }
    local_5c = local_58;
    local_2c = local_c0;
    iVar3 = Wvfm::unstop(local_c0);
    if (iVar3 != 1) {
      local_94 = local_58;
      local_90 = local_58;
      if (local_58 != (Wvfm *)0x0) {
        FUN_10019250(local_58,1);
      }
      local_9c = local_28;
      local_98 = local_28;
      if (local_28 != (Wvfm *)0x0) {
        FUN_10019250(local_28,1);
      }
      ExceptionList = local_10;
      return 0;
    }
    if ((*param_5 >> 5 & 1) == 0) {
      puVar4 = FUN_100266b0(local_a4,local_2c,local_18);
      uVar1 = puVar4[1];
      *(undefined4 *)local_18 = *puVar4;
      *(undefined4 *)(local_18 + 4) = uVar1;
      iVar3 = FUN_100158ca();
      if (iVar3 == 0) {
        ShftVect::ShftVect((ShftVect *)&local_64);
        *(undefined4 *)local_18 = local_64;
        *(undefined4 *)(local_18 + 4) = local_60;
      }
    }
    if ((*param_5 >> 7 & 1) == 0) {
      puVar4 = *(undefined4 **)((int)this + 0xa81c);
      *puVar4 = 0;
      puVar4[1] = 0x3ff00000;
      Wvfm::sort(local_5c);
      iVar3 = *(int *)((int)this + 0xa81c);
      *(undefined4 *)(iVar3 + 8) = 0;
      *(undefined4 *)(iVar3 + 0xc) = 0;
      local_54._0_4_ = 0;
      local_54._4_4_ = 0;
      for (local_24 = 1; local_24 < 5; local_24 = local_24 + 1) {
        dVar5 = Wvfm::sc_la(local_5c,2000,local_24);
        *(double *)(*(int *)((int)this + 0xa81c) + 8 + local_24 * 8) = dVar5;
      }
      Wvfm::operator=(local_5c,param_2);
      Wvfm::envelope(local_5c,local_18);
      for (local_24 = 1; iVar3 = local_24, local_24 < 5; local_24 = local_24 + 1) {
        *(undefined4 *)((int)&local_54 + local_24 * 2 * 4) = 0;
        local_4c[iVar3 * 2 + -1] = 0;
      }
      sVar2 = ShftVect::maxshft(local_18);
      local_14 = (uint)sVar2;
      while (local_14 = local_14 + 1, (int)local_14 <= param_3) {
        iVar3 = Wvfm::envi(local_5c,local_14);
        *(double *)((int)&local_54 + iVar3 * 2 * 4) =
             *(double *)((int)&local_54 + iVar3 * 2 * 4) + _DAT_10038f70;
      }
      for (local_24 = 1; iVar3 = local_24, local_24 < 5; local_24 = local_24 + 1) {
        sVar2 = ShftVect::maxshft(local_18);
        *(double *)((int)&local_54 + local_24 * 2 * 4) =
             *(double *)((int)&local_54 + iVar3 * 2 * 4) / (double)((param_3 - sVar2) + 1);
        if (*(double *)((int)&local_54 + local_24 * 2 * 4) < **(double **)((int)this + 0xa81c)) {
          *(int *)(*(int *)((int)this + 0xa81c) + 0x30) = local_24;
          puVar4 = *(undefined4 **)((int)this + 0xa81c);
          *puVar4 = *(undefined4 *)((int)&local_54 + local_24 * 2 * 4);
          puVar4[1] = local_4c[local_24 * 2 + -1];
        }
      }
      if (local_58 != (Wvfm *)0x0) {
        FUN_10019250(local_58,1);
      }
      if (local_28 != (Wvfm *)0x0) {
        FUN_10019250(local_28,1);
      }
      iVar3 = FUN_10033905(*(int *)((int)this + 0xa81c) + 8,4);
      if (iVar3 != 1) {
        ExceptionList = local_10;
        return 0;
      }
    }
  }
  if (((*param_5 >> 7 & 1) == 0) && (**(double **)((int)this + 0xa81c) < _DAT_10038f78)) {
    if (_DAT_10038f80 <=
        *(double *)
         (*(int *)((int)this + 0xa81c) + 8 + *(int *)(*(int *)((int)this + 0xa81c) + 0x30) * 8)) {
      local_e4 = 0x3fe80000;
    }
    else {
      local_e4 = 0x3fe00000;
    }
    local_20 = 0;
    local_1c = local_e4;
    local_6c = Wvfm::endi(param_1);
    local_68 = *(int *)(*(int *)((int)this + 0xa81c) + 0x30);
    for (local_14 = Wvfm::bgni(param_1); (int)local_14 <= local_6c; local_14 = local_14 + 1) {
      Wvfm::sc_la_mul(param_1,local_14,local_68,(double)CONCAT44(local_1c,local_20));
    }
  }
  ExceptionList = local_10;
  return 1;
}

//===== 0x10033905 =====

undefined4 __cdecl FUN_10033905(int param_1,size_t param_2)

{
  double dVar1;
  void *_Dst;
  undefined4 uVar2;
  int iVar3;
  undefined4 local_1c;
  undefined4 uStack_18;
  int local_14;
  int local_c;
  int local_8;
  
  _Dst = operator_new(param_2 << 4);
  if (_Dst == (void *)0x0) {
    uVar2 = 0;
  }
  else {
    memset(_Dst,0,param_2 << 4);
    for (local_8 = 1; local_8 <= (int)param_2; local_8 = local_8 + 1) {
      iVar3 = (local_8 + -1) * 0x10;
      *(undefined4 *)((int)_Dst + iVar3) = *(undefined4 *)(param_1 + local_8 * 8);
      *(undefined4 *)((int)_Dst + iVar3 + 4) = *(undefined4 *)(param_1 + 4 + local_8 * 8);
      *(int *)((int)_Dst + (local_8 + -1) * 0x10 + 8) = local_8;
    }
    qsort(_Dst,param_2,0x10,FUN_10033b0a);
    local_8 = 0;
    while (local_14 = local_8, local_8 < (int)param_2) {
      do {
        local_14 = local_14 + 1;
        if ((int)param_2 <= local_14) break;
      } while (*(double *)((int)_Dst + local_8 * 0x10) == *(double *)((int)_Dst + local_14 * 0x10));
      iVar3 = FUN_10033ac0(local_8 + 1,local_14);
      dVar1 = (double)iVar3 / (double)(local_14 - local_8);
      for (local_c = local_8; local_c < local_14; local_c = local_c + 1) {
        local_1c = SUB84(dVar1,0);
        *(undefined4 *)((int)_Dst + local_c * 0x10) = local_1c;
        uStack_18 = (undefined4)((ulonglong)dVar1 >> 0x20);
        *(undefined4 *)((int)_Dst + local_c * 0x10 + 4) = uStack_18;
      }
      local_8 = local_14;
    }
    for (local_8 = 0; local_8 < (int)param_2; local_8 = local_8 + 1) {
      iVar3 = *(int *)((int)_Dst + local_8 * 0x10 + 8);
      *(undefined4 *)(param_1 + iVar3 * 8) = *(undefined4 *)((int)_Dst + local_8 * 0x10);
      *(undefined4 *)(param_1 + 4 + iVar3 * 8) = *(undefined4 *)((int)_Dst + local_8 * 0x10 + 4);
    }
    operator_delete(_Dst);
    uVar2 = 1;
  }
  return uVar2;
}

//===== 0x10033ac0 =====

int __cdecl FUN_10033ac0(int param_1,int param_2)

{
  int iVar1;
  
  iVar1 = param_1;
  if (param_2 < param_1) {
    param_1 = param_2;
    param_2 = iVar1;
  }
  return (param_2 * (param_2 + 1)) / 2 - (param_1 * (param_1 + -1)) / 2;
}

//===== 0x10033b0a =====

undefined4 __cdecl FUN_10033b0a(double *param_1,double *param_2)

{
  undefined4 uVar1;
  
  if (*param_1 <= *param_2) {
    if (*param_2 <= *param_1) {
      uVar1 = 0;
    }
    else {
      uVar1 = 0xffffffff;
    }
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}

//===== 0x10033b58 =====

void FUN_10033b58(void)

{
  FUN_10033b62();
  return;
}

//===== 0x10033b62 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10033b62(void)

{
  _DAT_100425a0 = acos(-1.0);
  return;
}

//===== 0x10033b80 =====

void __cdecl FUN_10033b80(undefined4 param_1)

{
  fprintf((FILE *)(_iob_exref + 0x40),s_Numerical_Recipes_run_time_error_10041588);
  fprintf((FILE *)(_iob_exref + 0x40),&DAT_100415ac,param_1);
  fprintf((FILE *)(_iob_exref + 0x40),s____now_exiting_to_system____100415b0);
                    /* WARNING: Subroutine does not return */
  exit(1);
}

//===== 0x10033bda =====

/* float * __cdecl vector(long,long) */

float * __cdecl vector(long param_1,long param_2)

{
  void *pvVar1;
  
                    /* 0x33bda  431  ?vector@@YAPAMJJ@Z */
  pvVar1 = malloc((param_2 - param_1) * 4 + 8);
  if (pvVar1 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_in_vector___100415d0);
  }
  return (float *)((int)pvVar1 + param_1 * -4 + 4);
}

//===== 0x10033c1d =====

/* int * __cdecl ivector(long,long) */

int * __cdecl ivector(long param_1,long param_2)

{
  void *pvVar1;
  
                    /* 0x33c1d  252  ?ivector@@YAPAHJJ@Z */
  pvVar1 = malloc((param_2 - param_1) * 4 + 8);
  if (pvVar1 == (void *)0x0) {
    fprintf((FILE *)(_iob_exref + 0x40),s_ivector__nl__ld_nh__ld_v__p_100415f0,param_1,param_2,0);
    FUN_10033b80(s_ivector__allocation_failure_10041610);
  }
  return (int *)((int)pvVar1 + param_1 * -4 + 4);
}

//===== 0x10033c86 =====

int __cdecl FUN_10033c86(int param_1,int param_2)

{
  void *pvVar1;
  
  pvVar1 = malloc((param_2 - param_1) + 2);
  if (pvVar1 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_in_cvector___1004162c);
  }
  return (int)pvVar1 + (1 - param_1);
}

//===== 0x10033cc0 =====

/* unsigned long * __cdecl lvector(long,long) */

ulong * __cdecl lvector(long param_1,long param_2)

{
  void *pvVar1;
  
                    /* 0x33cc0  272  ?lvector@@YAPAKJJ@Z */
  pvVar1 = malloc((param_2 - param_1) * 4 + 8);
  if (pvVar1 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_in_lvector___1004164c);
  }
  return (ulong *)((int)pvVar1 + param_1 * -4 + 4);
}

//===== 0x10033d03 =====

/* double * __cdecl dvector(long,long) */

double * __cdecl dvector(long param_1,long param_2)

{
  void *pvVar1;
  
                    /* 0x33d03  148  ?dvector@@YAPANJJ@Z */
  pvVar1 = malloc((param_2 - param_1) * 8 + 0x10);
  if (pvVar1 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_in_dvector___1004166c);
  }
  return (double *)((int)pvVar1 + param_1 * -8 + 8);
}

//===== 0x10033d46 =====

/* float * * __cdecl matrix(long,long,long,long) */

float ** __cdecl matrix(long param_1,long param_2,long param_3,long param_4)

{
  int iVar1;
  void *pvVar2;
  float **ppfVar3;
  float *pfVar4;
  int iVar5;
  int local_10;
  
                    /* 0x33d46  274  ?matrix@@YAPAPAMJJJJ@Z */
  iVar1 = (param_2 - param_1) + 1;
  iVar5 = (param_4 - param_3) + 1;
  pvVar2 = malloc(iVar1 * 4 + 4);
  if (pvVar2 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_1_in_matrix___1004168c);
  }
  ppfVar3 = (float **)((int)pvVar2 + param_1 * -4 + 4);
  pfVar4 = malloc(iVar1 * iVar5 * 4 + 4);
  ppfVar3[param_1] = pfVar4;
  if (ppfVar3[param_1] == (float *)0x0) {
    FUN_10033b80(s_allocation_failure_2_in_matrix___100416b0);
  }
  ppfVar3[param_1] = ppfVar3[param_1] + 1;
  ppfVar3[param_1] = ppfVar3[param_1] + -param_3;
  while (local_10 = param_1 + 1, local_10 <= param_2) {
    ppfVar3[local_10] = ppfVar3[param_1] + iVar5;
    param_1 = local_10;
  }
  return ppfVar3;
}

//===== 0x10033e4c =====

/* double * * __cdecl dmatrix(long,long,long,long) */

double ** __cdecl dmatrix(long param_1,long param_2,long param_3,long param_4)

{
  int iVar1;
  void *pvVar2;
  double **ppdVar3;
  double *pdVar4;
  int iVar5;
  int local_10;
  
                    /* 0x33e4c  139  ?dmatrix@@YAPAPANJJJJ@Z */
  iVar1 = (param_2 - param_1) + 1;
  iVar5 = (param_4 - param_3) + 1;
  pvVar2 = malloc(iVar1 * 4 + 4);
  if (pvVar2 == (void *)0x0) {
    fprintf((FILE *)(_iob_exref + 0x40),s_nrl__ld__nrh__ld__ncl__ld__nch___100416d4,param_1,param_2,
            param_3,param_4,iVar1);
    FUN_10033b80(s_allocation_failure_1_in_dmatrix__10041704);
  }
  ppdVar3 = (double **)((int)pvVar2 + param_1 * -4 + 4);
  pdVar4 = malloc(iVar1 * iVar5 * 8 + 8);
  ppdVar3[param_1] = pdVar4;
  if (ppdVar3[param_1] == (double *)0x0) {
    FUN_10033b80(s_allocation_failure_2_in_dmatrix__10041728);
  }
  ppdVar3[param_1] = ppdVar3[param_1] + 1;
  ppdVar3[param_1] = ppdVar3[param_1] + -param_3;
  while (local_10 = param_1 + 1, local_10 <= param_2) {
    ppdVar3[local_10] = ppdVar3[param_1] + iVar5;
    param_1 = local_10;
  }
  return ppdVar3;
}

//===== 0x10033f7d =====

/* int * * __cdecl imatrix(long,long,long,long) */

int ** __cdecl imatrix(long param_1,long param_2,long param_3,long param_4)

{
  int iVar1;
  void *pvVar2;
  int **ppiVar3;
  int *piVar4;
  int iVar5;
  int local_10;
  
                    /* 0x33f7d  238  ?imatrix@@YAPAPAHJJJJ@Z */
  iVar1 = (param_2 - param_1) + 1;
  iVar5 = (param_4 - param_3) + 1;
  pvVar2 = malloc(iVar1 * 4 + 4);
  if (pvVar2 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_1_in_dmatrix__1004174c);
  }
  ppiVar3 = (int **)((int)pvVar2 + param_1 * -4 + 4);
  piVar4 = malloc(iVar1 * iVar5 * 4 + 4);
  ppiVar3[param_1] = piVar4;
  if (ppiVar3[param_1] == (int *)0x0) {
    FUN_10033b80(s_allocation_failure_2_in_imatrix__10041770);
  }
  ppiVar3[param_1] = ppiVar3[param_1] + 1;
  ppiVar3[param_1] = ppiVar3[param_1] + -param_3;
  while (local_10 = param_1 + 1, local_10 <= param_2) {
    ppiVar3[local_10] = ppiVar3[param_1] + iVar5;
    param_1 = local_10;
  }
  return ppiVar3;
}

//===== 0x10034083 =====

/* float * * __cdecl submatrix(float * *,long,long,long,long,long,long) */

float ** __cdecl
submatrix(float **param_1,long param_2,long param_3,long param_4,long param_5,long param_6,
         long param_7)

{
  void *pvVar1;
  float **ppfVar2;
  long local_14;
  long local_10;
  
                    /* 0x34083  419  ?submatrix@@YAPAPAMPAPAMJJJJJJ@Z */
  pvVar1 = malloc(((param_3 - param_2) + 1) * 4 + 4);
  if (pvVar1 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_in_submatrix__10041794);
  }
  ppfVar2 = (float **)((int)pvVar1 + param_6 * -4 + 4);
  local_14 = param_6;
  for (local_10 = param_2; local_10 <= param_3; local_10 = local_10 + 1) {
    ppfVar2[local_14] = param_1[local_10] + (param_5 - param_4) + 1;
    local_14 = local_14 + 1;
  }
  return ppfVar2;
}

//===== 0x1003412b =====

/* float * * __cdecl convert_matrix(float *,long,long,long,long) */

float ** __cdecl convert_matrix(float *param_1,long param_2,long param_3,long param_4,long param_5)

{
  int iVar1;
  void *pvVar2;
  float **ppfVar3;
  int local_14;
  int local_10;
  
                    /* 0x3412b  117  ?convert_matrix@@YAPAPAMPAMJJJJ@Z */
  iVar1 = (param_3 - param_2) + 1;
  pvVar2 = malloc(iVar1 * 4 + 4);
  if (pvVar2 == (void *)0x0) {
    FUN_10033b80(s_allocation_failure_in_convert_ma_100417b8);
  }
  ppfVar3 = (float **)((int)pvVar2 + param_2 * -4 + 4);
  ppfVar3[param_2] = param_1 + -param_4;
  for (local_10 = 1; local_14 = param_2 + 1, local_10 <= iVar1; local_10 = local_10 + 1) {
    ppfVar3[local_14] = ppfVar3[param_2] + (param_5 - param_4) + 1;
    param_2 = local_14;
  }
  return ppfVar3;
}

//===== 0x100341ec =====

/* void __cdecl free_vector(float *,long,long) */

void __cdecl free_vector(float *param_1,long param_2,long param_3)

{
                    /* 0x341ec  172  ?free_vector@@YAXPAMJJ@Z */
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x10034205 =====

/* void __cdecl free_ivector(int *,long,long) */

void __cdecl free_ivector(int *param_1,long param_2,long param_3)

{
                    /* 0x34205  169  ?free_ivector@@YAXPAHJJ@Z */
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x1003421e =====

/* void __cdecl free_cvector(unsigned char *,long,long) */

void __cdecl free_cvector(uchar *param_1,long param_2,long param_3)

{
                    /* 0x3421e  165  ?free_cvector@@YAXPAEJJ@Z */
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x10034237 =====

/* void __cdecl free_lvector(unsigned long *,long,long) */

void __cdecl free_lvector(ulong *param_1,long param_2,long param_3)

{
                    /* 0x34237  170  ?free_lvector@@YAXPAKJJ@Z */
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x10034250 =====

/* void __cdecl free_dvector(double *,long,long) */

void __cdecl free_dvector(double *param_1,long param_2,long param_3)

{
                    /* 0x34250  167  ?free_dvector@@YAXPANJJ@Z */
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x10034269 =====

/* void __cdecl free_matrix(float * *,long,long,long,long) */

void __cdecl free_matrix(float **param_1,long param_2,long param_3,long param_4,long param_5)

{
                    /* 0x34269  171  ?free_matrix@@YAXPAPAMJJJJ@Z */
  free(param_1[param_2] + param_4 + -1);
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x1003429c =====

/* void __cdecl free_dmatrix(double * *,long,long,long,long) */

void __cdecl free_dmatrix(double **param_1,long param_2,long param_3,long param_4,long param_5)

{
                    /* 0x3429c  166  ?free_dmatrix@@YAXPAPANJJJJ@Z */
  free(param_1[param_2] + param_4 + -1);
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x100342cf =====

/* void __cdecl free_imatrix(int * *,long,long,long,long) */

void __cdecl free_imatrix(int **param_1,long param_2,long param_3,long param_4,long param_5)

{
                    /* 0x342cf  168  ?free_imatrix@@YAXPAPAHJJJJ@Z */
  free(param_1[param_2] + param_4 + -1);
  free(param_1 + param_2 + -1);
  return;
}

//===== 0x10034302 =====

void __cdecl FUN_10034302(int param_1,int param_2)

{
  free((void *)(param_1 + -4 + param_2 * 4));
  return;
}

//===== 0x1003431b =====

void __cdecl FUN_1003431b(int param_1,int param_2)

{
  free((void *)(param_1 + -4 + param_2 * 4));
  return;
}

//===== 0x10034340 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* void __cdecl dfour1(double * const,unsigned long,int) */

void __cdecl dfour1(double *param_1,ulong param_2,int param_3)

{
  double dVar1;
  double dVar2;
  uint uVar3;
  uint uVar4;
  int iVar5;
  double dVar6;
  double dVar7;
  uint local_58;
  double local_54;
  uint local_4c;
  uint local_40;
  uint local_2c;
  double local_24;
  undefined4 local_c;
  undefined4 uStack_8;
  
                    /* 0x34340  137  ?dfour1@@YAXQANKH@Z */
  uVar4 = param_2 << 1;
  local_4c = 1;
  for (local_40 = 1; local_40 < uVar4; local_40 = local_40 + 2) {
    if (local_40 < local_4c) {
      dVar7 = param_1[local_4c];
      param_1[local_4c] = param_1[local_40];
      local_c = SUB84(dVar7,0);
      *(undefined4 *)(param_1 + local_40) = local_c;
      uStack_8 = (undefined4)((ulonglong)dVar7 >> 0x20);
      *(undefined4 *)((int)param_1 + local_40 * 8 + 4) = uStack_8;
      dVar7 = param_1[local_4c + 1];
      param_1[local_4c + 1] = param_1[local_40 + 1];
      local_c = SUB84(dVar7,0);
      *(undefined4 *)(param_1 + local_40 + 1) = local_c;
      uStack_8 = (undefined4)((ulonglong)dVar7 >> 0x20);
      *(undefined4 *)((int)param_1 + local_40 * 8 + 0xc) = uStack_8;
    }
    for (local_58 = param_2 & 0x7fffffff; (1 < local_58 && (local_58 < local_4c));
        local_58 = local_58 >> 1) {
      local_4c = local_4c - local_58;
    }
    local_4c = local_4c + local_58;
  }
  local_2c = 2;
  uVar3 = local_2c;
  while (local_2c = uVar3, local_2c < uVar4) {
    dVar7 = ((_DAT_10038f90 * _DAT_10042608) / (double)local_2c) * (double)param_3;
    dVar6 = sin(_DAT_10038f98 * dVar7);
    dVar6 = _DAT_10038fa0 * dVar6 * dVar6;
    dVar7 = sin(dVar7);
    local_24 = 1.0;
    local_54 = 0.0;
    for (local_58 = 1; uVar3 = local_2c * 2, local_58 < local_2c; local_58 = local_58 + 2) {
      for (local_40 = local_58; local_40 <= uVar4; local_40 = local_40 + local_2c * 2) {
        iVar5 = local_40 + local_2c;
        dVar1 = local_24 * param_1[iVar5] - local_54 * param_1[iVar5 + 1];
        dVar2 = local_54 * param_1[iVar5] + local_24 * param_1[iVar5 + 1];
        param_1[iVar5] = param_1[local_40] - dVar1;
        param_1[iVar5 + 1] = param_1[local_40 + 1] - dVar2;
        param_1[local_40] = param_1[local_40] + dVar1;
        param_1[local_40 + 1] = param_1[local_40 + 1] + dVar2;
      }
      dVar1 = local_54 * dVar7;
      local_54 = local_24 * dVar7 + local_54 * dVar6 + local_54;
      local_24 = (local_24 * dVar6 - dVar1) + local_24;
    }
  }
  return;
}

//===== 0x100345d6 =====

void FUN_100345d6(void)

{
  FUN_100345e0();
  return;
}

//===== 0x100345e0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_100345e0(void)

{
  _DAT_10042608 = acos(-1.0);
  return;
}

//===== 0x10034600 =====

undefined4 * __thiscall FUN_10034600(void *this,undefined4 *param_1)

{
  if (this != param_1) {
    *(undefined4 *)this = *param_1;
    *(undefined4 *)((int)this + 4) = param_1[1];
    *(undefined4 *)((int)this + 8) = param_1[2];
    *(undefined4 *)((int)this + 0xc) = param_1[3];
  }
  return this;
}

//===== 0x1003463a =====

void * __thiscall FUN_1003463a(void *this,void *param_1,double *param_2)

{
  double local_14;
  double local_c;
  
  FUN_1000c100(&local_14,0,0,0,0);
  local_14 = *(double *)this + *param_2;
  local_c = *(double *)((int)this + 8) + param_2[1];
  FUN_10034bc0(param_1,(undefined4 *)&local_14);
  BandStat::~BandStat((BandStat *)&local_14);
  return param_1;
}

//===== 0x1003468c =====

void * __thiscall FUN_1003468c(void *this,double *param_1)

{
  undefined4 *puVar1;
  BandStat local_14 [16];
  
  puVar1 = FUN_1003463a(this,local_14,param_1);
  FUN_10034600(this,puVar1);
  BandStat::~BandStat(local_14);
  return this;
}

//===== 0x100346bf =====

void * __thiscall FUN_100346bf(void *this,void *param_1,double *param_2)

{
  double local_14;
  double local_c;
  
  FUN_1000c100(&local_14,0,0,0,0);
  local_14 = *(double *)this * *param_2 - *(double *)((int)this + 8) * param_2[1];
  local_c = *(double *)this * param_2[1] + *(double *)((int)this + 8) * *param_2;
  FUN_10034bc0(param_1,(undefined4 *)&local_14);
  BandStat::~BandStat((BandStat *)&local_14);
  return param_1;
}

//===== 0x1003472b =====

void * __thiscall FUN_1003472b(void *this,double *param_1)

{
  undefined4 *puVar1;
  BandStat local_14 [16];
  
  puVar1 = FUN_100346bf(this,local_14,param_1);
  FUN_10034600(this,puVar1);
  BandStat::~BandStat(local_14);
  return this;
}

//===== 0x1003475e =====

void * __thiscall FUN_1003475e(void *this,void *param_1,double *param_2)

{
  double local_14;
  double local_c;
  
  FUN_1000c100(&local_14,0,0,0,0);
  local_14 = *(double *)this - *param_2;
  local_c = *(double *)((int)this + 8) - param_2[1];
  FUN_10034bc0(param_1,(undefined4 *)&local_14);
  BandStat::~BandStat((BandStat *)&local_14);
  return param_1;
}

//===== 0x100347b0 =====

void * __thiscall FUN_100347b0(void *this,double *param_1)

{
  undefined4 *puVar1;
  BandStat local_14 [16];
  
  puVar1 = FUN_1003475e(this,local_14,param_1);
  FUN_10034600(this,puVar1);
  BandStat::~BandStat(local_14);
  return this;
}

//===== 0x100347e3 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void * __thiscall FUN_100347e3(void *this,void *param_1,double *param_2)

{
  double dVar1;
  double dVar2;
  double local_1c;
  double local_14;
  double local_c;
  
  FUN_1000c100(&local_1c,0,0,0,0);
  dVar1 = fabs(*param_2);
  dVar2 = fabs(param_2[1]);
  if (dVar1 < dVar2) {
    if (_DAT_10038fa8 == param_2[1]) {
      FUN_10034bc0(param_1,(undefined4 *)&local_1c);
      BandStat::~BandStat((BandStat *)&local_1c);
      return param_1;
    }
    local_c = *param_2 / param_2[1];
    local_14 = local_c * *param_2 + param_2[1];
    if (_DAT_10038fa8 == local_14) {
      FUN_10034bc0(param_1,(undefined4 *)&local_1c);
      BandStat::~BandStat((BandStat *)&local_1c);
      return param_1;
    }
    local_1c = (local_c * *(double *)this + *(double *)((int)this + 8)) / local_14;
    local_14 = (local_c * *(double *)((int)this + 8) - *(double *)this) / local_14;
  }
  else {
    if (_DAT_10038fa8 == *param_2) {
      FUN_10034bc0(param_1,(undefined4 *)&local_1c);
      BandStat::~BandStat((BandStat *)&local_1c);
      return param_1;
    }
    local_c = param_2[1] / *param_2;
    local_14 = local_c * param_2[1] + *param_2;
    if (_DAT_10038fa8 == local_14) {
      FUN_10034bc0(param_1,(undefined4 *)&local_1c);
      BandStat::~BandStat((BandStat *)&local_1c);
      return param_1;
    }
    local_1c = (local_c * *(double *)((int)this + 8) + *(double *)this) / local_14;
    local_14 = (*(double *)((int)this + 8) - local_c * *(double *)this) / local_14;
  }
  FUN_10034bc0(param_1,(undefined4 *)&local_1c);
  BandStat::~BandStat((BandStat *)&local_1c);
  return param_1;
}

//===== 0x10034994 =====

void * __thiscall FUN_10034994(void *this,double *param_1)

{
  undefined4 *puVar1;
  BandStat local_14 [16];
  
  puVar1 = FUN_100347e3(this,local_14,param_1);
  FUN_10034600(this,puVar1);
  BandStat::~BandStat(local_14);
  return this;
}

//===== 0x100349c7 =====

void __fastcall FUN_100349c7(double *param_1)

{
  double dVar1;
  double dVar2;
  
  dVar1 = exp(*param_1);
  dVar2 = cos(param_1[1]);
  *param_1 = dVar2 * dVar1;
  dVar2 = sin(param_1[1]);
  param_1[1] = dVar2 * dVar1;
  return;
}

//===== 0x10034a20 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __fastcall FUN_10034a20(double *param_1)

{
  float10 fVar1;
  double dVar2;
  
  fVar1 = FUN_10034c00(param_1);
  dVar2 = log(param_1[1] * param_1[1] + *param_1 * *param_1);
  *param_1 = dVar2 * _DAT_10038fb0;
  param_1[1] = (double)fVar1;
  return;
}

//===== 0x10034a78 =====

void __fastcall FUN_10034a78(int param_1)

{
  *(double *)(param_1 + 8) = -*(double *)(param_1 + 8);
  return;
}

//===== 0x10034a91 =====

void __thiscall FUN_10034a91(void *this,double param_1)

{
  *(double *)this = *(double *)this * param_1;
  *(double *)((int)this + 8) = *(double *)((int)this + 8) * param_1;
  return;
}

//===== 0x10034aba =====

void __fastcall FUN_10034aba(double *param_1)

{
  double dVar1;
  
  dVar1 = param_1[1] * param_1[1] + *param_1 * *param_1;
  *param_1 = *param_1 / dVar1;
  param_1[1] = -param_1[1] / dVar1;
  return;
}

//===== 0x10034b00 =====

void __cdecl FUN_10034b00(int param_1,int param_2,int param_3,int param_4)

{
  undefined4 *puVar1;
  BandStat local_24 [16];
  int local_14;
  int local_10;
  int local_c;
  int local_8;
  
  local_c = param_1 + -8;
  local_10 = param_2 + -8;
  local_14 = param_3 + -8;
  for (local_8 = 1; local_8 <= param_4; local_8 = local_8 + 1) {
    puVar1 = FUN_100346bf((void *)(local_c + local_8 * 0x10),local_24,
                          (double *)(local_10 + local_8 * 0x10));
    FUN_10034600((void *)(local_14 + local_8 * 0x10),puVar1);
    BandStat::~BandStat(local_24);
  }
  return;
}

//===== 0x10034b7a =====

void __cdecl FUN_10034b7a(int param_1,int param_2)

{
  undefined4 local_c;
  
  for (local_c = 1; local_c <= param_2; local_c = local_c + 1) {
    FUN_10034aba((double *)(param_1 + -8 + local_c * 0x10));
  }
  return;
}

//===== 0x10034bc0 =====

undefined4 * __thiscall FUN_10034bc0(void *this,undefined4 *param_1)

{
  *(undefined4 *)this = 0;
  *(undefined4 *)((int)this + 4) = 0;
  *(undefined4 *)((int)this + 8) = 0;
  *(undefined4 *)((int)this + 0xc) = 0;
  FUN_10034600(this,param_1);
  return this;
}

//===== 0x10034c00 =====

float10 __fastcall FUN_10034c00(double *param_1)

{
  double dVar1;
  
  dVar1 = atan2(param_1[1],*param_1);
  return (float10)dVar1;
}

//===== 0x10034c30 =====

/* int __cdecl ilinreg(int const *,int const *,int,float * const,float *) */

int __cdecl ilinreg(int *param_1,int *param_2,int param_3,float *param_4,float *param_5)

{
  int iVar1;
  float fVar2;
  float fVar3;
  float fVar4;
  float fVar5;
  float fVar6;
  float fVar7;
  int iVar8;
  float **ppfVar9;
  float **ppfVar10;
  int local_8;
  
                    /* 0x34c30  237  ?ilinreg@@YAHPBH0HQAMPAM@Z */
  fVar4 = 0.0;
  fVar5 = 0.0;
  fVar6 = 0.0;
  param_4[2] = 0.0;
  param_4[1] = 0.0;
  *param_4 = 0.0;
  if (param_3 < 2) {
    iVar8 = 0;
  }
  else {
    ppfVar9 = matrix(1,2,1,2);
    if (ppfVar9 == (float **)0x0) {
      iVar8 = 0;
    }
    else {
      ppfVar10 = matrix(1,2,1,1);
      if (ppfVar10 == (float **)0x0) {
        if (ppfVar9 != (float **)0x0) {
          free_matrix(ppfVar9,1,2,1,2);
        }
        iVar8 = 0;
      }
      else {
        ppfVar10[2][1] = 0.0;
        ppfVar10[1][1] = 0.0;
        fVar7 = 0.0;
        fVar3 = 0.0;
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          iVar8 = param_1[local_8];
          fVar2 = (float)iVar8;
          iVar1 = param_2[local_8];
          fVar3 = fVar3 + fVar2;
          fVar7 = fVar2 * fVar2 + fVar7;
          ppfVar10[1][1] = (float)iVar1 + ppfVar10[1][1];
          ppfVar10[2][1] = (float)iVar8 * (float)iVar1 + ppfVar10[2][1];
        }
        fVar2 = ppfVar10[1][1] / (float)param_3;
        ppfVar9[1][1] = (float)param_3;
        ppfVar9[2][1] = fVar3;
        ppfVar9[1][2] = ppfVar9[2][1];
        ppfVar9[2][2] = fVar7;
        FUN_100364a0((int)ppfVar9,2,(int)ppfVar10,1);
        *param_4 = ppfVar10[1][1];
        param_4[1] = ppfVar10[2][1];
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          fVar3 = param_4[1] * (float)param_1[local_8] + *param_4;
          iVar8 = param_2[local_8];
          fVar4 = ((float)iVar8 - fVar2) * ((float)iVar8 - fVar2) + fVar4;
          fVar5 = (fVar3 - fVar2) * (fVar3 - fVar2) + fVar5;
          fVar6 = ((float)iVar8 - fVar3) * ((float)iVar8 - fVar3) + fVar6;
        }
        if (2 < param_3) {
          param_4[2] = fVar6 / (float)(param_3 + -2);
        }
        if (param_5 != (float *)0x0) {
          *param_5 = fVar5 / fVar4;
        }
        free_matrix(ppfVar9,1,2,1,2);
        free_matrix(ppfVar10,1,2,1,1);
        iVar8 = 1;
      }
    }
  }
  return iVar8;
}

//===== 0x10034eef =====

/* int __cdecl linreg(float const *,float const *,int,float * const,float *) */

int __cdecl linreg(float *param_1,float *param_2,int param_3,float *param_4,float *param_5)

{
  float fVar1;
  float fVar2;
  float fVar3;
  float fVar4;
  float fVar5;
  float fVar6;
  float fVar7;
  int iVar8;
  float **ppfVar9;
  float **ppfVar10;
  int local_8;
  
                    /* 0x34eef  264  ?linreg@@YAHPBM0HQAMPAM@Z */
  fVar5 = 0.0;
  fVar6 = 0.0;
  fVar7 = 0.0;
  param_4[2] = 0.0;
  param_4[1] = 0.0;
  *param_4 = 0.0;
  if (param_3 < 2) {
    iVar8 = 0;
  }
  else {
    ppfVar9 = matrix(1,2,1,2);
    if (ppfVar9 == (float **)0x0) {
      iVar8 = 0;
    }
    else {
      ppfVar10 = matrix(1,2,1,1);
      if (ppfVar10 == (float **)0x0) {
        if (ppfVar9 != (float **)0x0) {
          free_matrix(ppfVar9,1,2,1,2);
        }
        iVar8 = 0;
      }
      else {
        ppfVar10[2][1] = 0.0;
        ppfVar10[1][1] = 0.0;
        fVar4 = 0.0;
        fVar1 = 0.0;
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          fVar2 = param_1[local_8];
          fVar3 = param_2[local_8];
          fVar1 = fVar2 + fVar1;
          fVar4 = fVar2 * fVar2 + fVar4;
          ppfVar10[1][1] = ppfVar10[1][1] + fVar3;
          ppfVar10[2][1] = fVar2 * fVar3 + ppfVar10[2][1];
        }
        fVar2 = ppfVar10[1][1] / (float)param_3;
        ppfVar9[1][1] = (float)param_3;
        ppfVar9[2][1] = fVar1;
        ppfVar9[1][2] = ppfVar9[2][1];
        ppfVar9[2][2] = fVar4;
        FUN_100364a0((int)ppfVar9,2,(int)ppfVar10,1);
        *param_4 = ppfVar10[1][1];
        param_4[1] = ppfVar10[2][1];
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          fVar4 = param_4[1] * param_1[local_8] + *param_4;
          fVar1 = param_2[local_8];
          fVar5 = (fVar1 - fVar2) * (fVar1 - fVar2) + fVar5;
          fVar6 = (fVar4 - fVar2) * (fVar4 - fVar2) + fVar6;
          fVar7 = (fVar1 - fVar4) * (fVar1 - fVar4) + fVar7;
        }
        if (2 < param_3) {
          param_4[2] = fVar7 / (float)(param_3 + -2);
        }
        if (param_5 != (float *)0x0) {
          *param_5 = fVar6 / fVar5;
        }
        free_matrix(ppfVar9,1,2,1,2);
        free_matrix(ppfVar10,1,2,1,1);
        iVar8 = 1;
      }
    }
  }
  return iVar8;
}

//===== 0x100351a8 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* int __cdecl iquadratic(int const *,int const *,int,float * const) */

int __cdecl iquadratic(int *param_1,int *param_2,int param_3,float *param_4)

{
  int iVar1;
  double dVar2;
  float fVar3;
  float fVar4;
  int iVar5;
  float **ppfVar6;
  float **ppfVar7;
  double local_3c;
  double local_30;
  double local_20;
  double local_18;
  double local_10;
  int local_8;
  
                    /* 0x351a8  244  ?iquadratic@@YAHPBH0HQAM@Z */
  param_4[3] = 0.0;
  param_4[2] = 0.0;
  param_4[1] = 0.0;
  *param_4 = 0.0;
  if (param_3 < 4) {
    iVar5 = 0;
  }
  else {
    ppfVar6 = matrix(1,3,1,3);
    if (ppfVar6 == (float **)0x0) {
      iVar5 = 0;
    }
    else {
      ppfVar7 = matrix(1,3,1,1);
      if (ppfVar7 == (float **)0x0) {
        free_matrix(ppfVar6,1,3,1,3);
        iVar5 = 0;
      }
      else {
        ppfVar7[3][1] = 0.0;
        ppfVar7[2][1] = 0.0;
        ppfVar7[1][1] = 0.0;
        local_30 = 0.0;
        local_20 = 0.0;
        local_18 = 0.0;
        local_3c = 0.0;
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          iVar5 = param_1[local_8];
          dVar2 = (double)iVar5;
          iVar1 = param_2[local_8];
          local_3c = local_3c + dVar2;
          local_18 = dVar2 * dVar2 + local_18;
          local_20 = dVar2 * dVar2 * dVar2 + local_20;
          local_30 = dVar2 * dVar2 * dVar2 * dVar2 + local_30;
          ppfVar7[1][1] = (float)iVar1 + ppfVar7[1][1];
          ppfVar7[2][1] = (float)iVar5 * (float)iVar1 + ppfVar7[2][1];
          ppfVar7[3][1] = (float)iVar5 * (float)iVar5 * (float)iVar1 + ppfVar7[3][1];
        }
        dVar2 = (double)(ppfVar7[1][1] / (float)param_3);
        local_10 = 0.0;
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          local_10 = ((double)param_2[local_8] - dVar2) * ((double)param_2[local_8] - dVar2) +
                     local_10;
        }
        local_10 = local_10 / (double)(param_3 + -1);
        if (_DAT_10038fb8 == local_10) {
          *param_4 = ppfVar7[1][1] / (float)param_3;
        }
        else {
          ppfVar7[1][1] = ppfVar7[1][1] / (float)local_10;
          ppfVar7[2][1] = ppfVar7[2][1] / (float)local_10;
          ppfVar7[3][1] = ppfVar7[3][1] / (float)local_10;
          ppfVar6[1][1] = (float)param_3 / (float)local_10;
          ppfVar6[2][1] = (float)((float10)local_3c / (float10)local_10);
          ppfVar6[1][2] = ppfVar6[2][1];
          ppfVar6[3][1] = (float)((float10)local_18 / (float10)local_10);
          ppfVar6[2][2] = ppfVar6[3][1];
          ppfVar6[1][3] = ppfVar6[2][2];
          ppfVar6[3][2] = (float)((float10)local_20 / (float10)local_10);
          ppfVar6[2][3] = ppfVar6[3][2];
          ppfVar6[3][3] = (float)((float10)local_30 / (float10)local_10);
          FUN_100364a0((int)ppfVar6,3,(int)ppfVar7,1);
          fVar4 = 0.0;
          for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
            fVar3 = (float)param_1[local_8];
            fVar3 = ppfVar7[3][1] * fVar3 * fVar3 + ppfVar7[2][1] * fVar3 + ppfVar7[1][1];
            fVar4 = (fVar3 - (float)param_2[local_8]) * (fVar3 - (float)param_2[local_8]) + fVar4;
          }
          *param_4 = ppfVar7[1][1];
          param_4[1] = ppfVar7[2][1];
          param_4[2] = ppfVar7[3][1];
          param_4[3] = fVar4 / (float)(param_3 + -3);
        }
        free_matrix(ppfVar6,1,3,1,3);
        free_matrix(ppfVar7,1,3,1,1);
        iVar5 = 1;
      }
    }
  }
  return iVar5;
}

//===== 0x100355e2 =====

void FUN_100355e2(void)

{
  FUN_100355ec();
  return;
}

//===== 0x100355ec =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_100355ec(void)

{
  _DAT_10042670 = acos(-1.0);
  return;
}

//===== 0x10035606 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* int __cdecl dquadratic(double const *,double const *,int,float * const) */

int __cdecl dquadratic(double *param_1,double *param_2,int param_3,float *param_4)

{
  double dVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  int iVar6;
  float **ppfVar7;
  float **ppfVar8;
  double local_3c;
  double local_30;
  double local_20;
  double local_18;
  double local_10;
  int local_8;
  
                    /* 0x35606  145  ?dquadratic@@YAHPBN0HQAM@Z */
  param_4[3] = 0.0;
  param_4[2] = 0.0;
  param_4[1] = 0.0;
  *param_4 = 0.0;
  if (param_3 < 4) {
    iVar6 = 0;
  }
  else {
    ppfVar7 = matrix(1,3,1,3);
    if (ppfVar7 == (float **)0x0) {
      iVar6 = 0;
    }
    else {
      ppfVar8 = matrix(1,3,1,1);
      if (ppfVar8 == (float **)0x0) {
        free_matrix(ppfVar7,1,3,1,3);
        iVar6 = 0;
      }
      else {
        ppfVar8[3][1] = 0.0;
        ppfVar8[2][1] = 0.0;
        ppfVar8[1][1] = 0.0;
        local_30 = 0.0;
        local_20 = 0.0;
        local_18 = 0.0;
        local_3c = 0.0;
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          uVar2 = *(undefined4 *)(param_1 + local_8);
          uVar3 = *(undefined4 *)((int)param_1 + local_8 * 8 + 4);
          uVar4 = *(undefined4 *)(param_2 + local_8);
          uVar5 = *(undefined4 *)((int)param_2 + local_8 * 8 + 4);
          local_3c = local_3c + (double)CONCAT44(uVar3,uVar2);
          local_18 = (double)CONCAT44(uVar3,uVar2) * (double)CONCAT44(uVar3,uVar2) + local_18;
          local_20 = (double)CONCAT44(uVar3,uVar2) * (double)CONCAT44(uVar3,uVar2) *
                     (double)CONCAT44(uVar3,uVar2) + local_20;
          local_30 = (double)CONCAT44(uVar3,uVar2) * (double)CONCAT44(uVar3,uVar2) *
                     (double)CONCAT44(uVar3,uVar2) * (double)CONCAT44(uVar3,uVar2) + local_30;
          ppfVar8[1][1] = (float)(double)CONCAT44(uVar5,uVar4) + ppfVar8[1][1];
          ppfVar8[2][1] =
               (float)((float10)(double)CONCAT44(uVar3,uVar2) *
                       (float10)(double)CONCAT44(uVar5,uVar4) + (float10)ppfVar8[2][1]);
          ppfVar8[3][1] =
               (float)((float10)(double)CONCAT44(uVar3,uVar2) *
                       (float10)(double)CONCAT44(uVar3,uVar2) *
                       (float10)(double)CONCAT44(uVar5,uVar4) + (float10)ppfVar8[3][1]);
        }
        dVar1 = (double)(ppfVar8[1][1] / (float)param_3);
        local_10 = 0.0;
        for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
          uVar2 = *(undefined4 *)((int)param_2 + local_8 * 8 + 4);
          local_10 = ((double)CONCAT44(uVar2,*(undefined4 *)(param_2 + local_8)) - dVar1) *
                     ((double)CONCAT44(uVar2,*(undefined4 *)(param_2 + local_8)) - dVar1) + local_10
          ;
        }
        local_10 = local_10 / (double)(param_3 + -1);
        if (_DAT_10038fb8 == local_10) {
          *param_4 = ppfVar8[1][1] / (float)param_3;
          param_4[3] = 0.0;
          param_4[2] = 0.0;
          param_4[1] = 0.0;
        }
        else {
          ppfVar8[1][1] = ppfVar8[1][1] / (float)local_10;
          ppfVar8[2][1] = ppfVar8[2][1] / (float)local_10;
          ppfVar8[3][1] = ppfVar8[3][1] / (float)local_10;
          ppfVar7[1][1] = (float)param_3 / (float)local_10;
          ppfVar7[2][1] = (float)((float10)local_3c / (float10)local_10);
          ppfVar7[1][2] = ppfVar7[2][1];
          ppfVar7[3][1] = (float)((float10)local_18 / (float10)local_10);
          ppfVar7[2][2] = ppfVar7[3][1];
          ppfVar7[1][3] = ppfVar7[2][2];
          ppfVar7[3][2] = (float)((float10)local_20 / (float10)local_10);
          ppfVar7[2][3] = ppfVar7[3][2];
          ppfVar7[3][3] = (float)((float10)local_30 / (float10)local_10);
          FUN_100364a0((int)ppfVar7,3,(int)ppfVar8,1);
          local_10 = 0.0;
          for (local_8 = 1; local_8 <= param_3; local_8 = local_8 + 1) {
            uVar2 = *(undefined4 *)(param_1 + local_8);
            uVar3 = *(undefined4 *)((int)param_1 + local_8 * 8 + 4);
            uVar4 = *(undefined4 *)((int)param_2 + local_8 * 8 + 4);
            dVar1 = (double)ppfVar8[3][1] * (double)CONCAT44(uVar3,uVar2) *
                    (double)CONCAT44(uVar3,uVar2) +
                    (double)ppfVar8[2][1] * (double)CONCAT44(uVar3,uVar2) + (double)ppfVar8[1][1];
            local_10 = (dVar1 - (double)CONCAT44(uVar4,*(undefined4 *)(param_2 + local_8))) *
                       (dVar1 - (double)CONCAT44(uVar4,*(undefined4 *)(param_2 + local_8))) +
                       local_10;
          }
          *param_4 = ppfVar8[1][1];
          param_4[1] = ppfVar8[2][1];
          param_4[2] = ppfVar8[3][1];
          param_4[3] = (float)local_10 / (float)(param_3 + -3);
        }
        free_matrix(ppfVar7,1,3,1,3);
        free_matrix(ppfVar8,1,3,1,1);
        iVar6 = _finite((double)param_4[3]);
        if (iVar6 == 0) {
          param_4[3] = 1e+06;
        }
        iVar6 = 1;
      }
    }
  }
  return iVar6;
}

//===== 0x10035ab0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* double __cdecl corrcoef(float const *,float const *,int) */

double __cdecl corrcoef(float *param_1,float *param_2,int param_3)

{
  double dVar1;
  double dVar2;
  float fVar3;
  float fVar4;
  double dVar5;
  double local_20;
  double local_18;
  double local_10;
  int local_8;
  
                    /* 0x35ab0  118  ?corrcoef@@YANPBM0H@Z */
  dVar5 = _DAT_10038fc0;
  if (1 < param_3) {
    fVar4 = 0.0;
    fVar3 = 0.0;
    for (local_8 = 0; local_8 < param_3; local_8 = local_8 + 1) {
      fVar3 = param_1[local_8] + fVar3;
      fVar4 = param_2[local_8] + fVar4;
    }
    local_10 = 0.0;
    local_18 = 0.0;
    local_20 = 0.0;
    for (local_8 = 0; local_8 < param_3; local_8 = local_8 + 1) {
      dVar1 = (double)(param_1[local_8] - fVar3 / (float)param_3);
      dVar2 = (double)(param_2[local_8] - fVar4 / (float)param_3);
      local_20 = dVar1 * dVar2 + local_20;
      local_18 = dVar1 * dVar1 + local_18;
      local_10 = dVar2 * dVar2 + local_10;
    }
    dVar1 = (double)param_3 - _DAT_10038fc8;
    local_18 = local_18 / ((double)param_3 - _DAT_10038fc8);
    local_10 = local_10 / ((double)param_3 - _DAT_10038fc8);
    if ((_DAT_10038fc0 != local_18) && (_DAT_10038fc0 != local_10)) {
      dVar5 = sqrt(local_18 * local_10);
      dVar5 = (local_20 / dVar1) / dVar5;
    }
  }
  return dVar5;
}

//===== 0x10035c21 =====

void FUN_10035c21(void)

{
  FUN_10035c2b();
  return;
}

//===== 0x10035c2b =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10035c2b(void)

{
  _DAT_100426d8 = acos(-1.0);
  return;
}

//===== 0x10035c50 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* int __cdecl polfit(float const *,float const *,float const *,int,int,enum PFWGHT,float *
   const,float &) */

int __cdecl
polfit(float *param_1,float *param_2,float *param_3,int param_4,int param_5,PFWGHT param_6,
      float *param_7,float *param_8)

{
  float fVar1;
  double dVar2;
  int iVar3;
  double *pdVar4;
  double *pdVar5;
  float **ppfVar6;
  float **ppfVar7;
  double local_58;
  double local_40;
  double local_38;
  double local_2c;
  int local_14;
  int local_10;
  
                    /* 0x35c50  302  ?polfit@@YAHPBM00HHW4PFWGHT@@QAMAAM@Z */
  if (param_4 < 2) {
    iVar3 = 1;
  }
  else {
    iVar3 = param_5 * 2 + -1;
    pdVar4 = dvector(1,iVar3);
    pdVar5 = dvector(1,param_5);
    ppfVar6 = matrix(1,param_5,1,1);
    ppfVar7 = matrix(1,param_5,1,param_5);
    for (local_14 = 1; local_14 <= iVar3; local_14 = local_14 + 1) {
      *(undefined4 *)(pdVar4 + local_14) = 0;
      *(undefined4 *)((int)pdVar4 + local_14 * 8 + 4) = 0;
    }
    for (local_14 = 1; local_14 <= param_5; local_14 = local_14 + 1) {
      *(undefined4 *)(pdVar5 + local_14) = 0;
      *(undefined4 *)((int)pdVar5 + local_14 * 8 + 4) = 0;
    }
    local_2c = 0.0;
    for (local_14 = 1; local_14 <= param_4; local_14 = local_14 + 1) {
      fVar1 = param_1[local_14];
      dVar2 = (double)param_2[local_14];
      if (param_6 == 0xffffffff) {
        if (_DAT_10038fd0 <= dVar2) {
          if (_DAT_10038fd0 == dVar2) {
            local_40 = 1.0;
          }
          else {
            local_40 = _DAT_10038fe0 / dVar2;
          }
        }
        else {
          local_40 = _DAT_10038fd8 / dVar2;
        }
      }
      else if (param_6 == 0) {
        local_40 = 1.0;
      }
      else if (param_6 == 1) {
        local_40 = (double)((float)_DAT_10038fe0 / (param_3[local_14] * param_3[local_14]));
      }
      local_58 = local_40;
      for (local_10 = 1; local_10 <= iVar3; local_10 = local_10 + 1) {
        pdVar4[local_10] = pdVar4[local_10] + local_58;
        local_58 = local_58 * (double)fVar1;
      }
      local_38 = local_40 * dVar2;
      for (local_10 = 1; local_10 <= param_5; local_10 = local_10 + 1) {
        pdVar5[local_10] = pdVar5[local_10] + local_38;
        local_38 = local_38 * (double)fVar1;
      }
      local_2c = local_40 * dVar2 * dVar2 + local_2c;
    }
    for (local_14 = 1; local_14 <= param_5; local_14 = local_14 + 1) {
      ppfVar6[local_14][1] = (float)pdVar5[local_14];
      for (local_10 = 1; local_10 <= param_5; local_10 = local_10 + 1) {
        ppfVar7[local_14][local_10] = (float)pdVar4[local_14 + local_10 + -1];
      }
    }
    FUN_100364a0((int)ppfVar7,param_5,(int)ppfVar6,1);
    for (local_14 = 1; local_14 <= param_5; local_14 = local_14 + 1) {
      param_7[local_14] = ppfVar6[local_14][1];
      fVar1 = (float)local_2c -
              ppfVar6[local_14][1] * (float)pdVar5[local_14] * (float)_DAT_10038fe8;
      for (local_10 = 1; local_2c = (double)fVar1, local_10 <= param_5; local_10 = local_10 + 1) {
        fVar1 = ppfVar6[local_14][1] * ppfVar6[local_10][1] *
                (float)pdVar4[local_14 + local_10 + -1] + fVar1;
      }
    }
    free_dvector(pdVar4,1,iVar3);
    free_dvector(pdVar5,1,param_5);
    free_matrix(ppfVar6,1,param_5,1,1);
    free_matrix(ppfVar7,1,param_5,1,param_5);
    if ((double)(param_4 - param_5) == _DAT_10038fd0) {
      iVar3 = 1;
    }
    else {
      *param_8 = (float)local_2c / (float)(param_4 - param_5);
      iVar3 = 0;
    }
  }
  return iVar3;
}

//===== 0x1003603f =====

void FUN_1003603f(void)

{
  FUN_10036049();
  return;
}

//===== 0x10036049 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10036049(void)

{
  _DAT_10042740 = acos(-1.0);
  return;
}

//===== 0x10036070 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* void __cdecl spline(float const * const,float const * const,int,float,float,float * const) */

void __cdecl
spline(float *param_1,float *param_2,int param_3,float param_4,float param_5,float *param_6)

{
  float fVar1;
  float fVar2;
  int iVar3;
  float *pfVar4;
  int local_18;
  int local_14;
  float local_10;
  float local_c;
  
                    /* 0x36070  407  ?spline@@YAXQBM0HMMQAM@Z */
  pfVar4 = vector(1,param_3 + -1);
  if (param_4 <= (float)_DAT_10038ff0) {
    param_6[1] = -0.5;
    pfVar4[1] = ((param_2[2] - param_2[1]) / (param_1[2] - param_1[1]) - param_4) *
                (_DAT_10038ff8 / (param_1[2] - param_1[1]));
  }
  else {
    pfVar4[1] = 0.0;
    param_6[1] = 0.0;
  }
  for (local_14 = 2; local_14 <= param_3 + -1; local_14 = local_14 + 1) {
    fVar1 = (param_1[local_14] - param_1[local_14 + -1]) /
            (param_1[local_14 + 1] - param_1[local_14 + -1]);
    fVar2 = fVar1 * param_6[local_14 + -1] + _DAT_10038ffc;
    param_6[local_14] = (fVar1 - _DAT_10039000) / fVar2;
    pfVar4[local_14] =
         (param_2[local_14 + 1] - param_2[local_14]) / (param_1[local_14 + 1] - param_1[local_14]) -
         (param_2[local_14] - param_2[local_14 + -1]) / (param_1[local_14] - param_1[local_14 + -1])
    ;
    pfVar4[local_14] =
         ((_DAT_10039004 * pfVar4[local_14]) / (param_1[local_14 + 1] - param_1[local_14 + -1]) -
         fVar1 * pfVar4[local_14 + -1]) / fVar2;
  }
  if (param_5 <= (float)_DAT_10038ff0) {
    local_10 = 0.5;
    local_c = (param_5 -
              (param_2[param_3] - param_2[param_3 + -1]) /
              (param_1[param_3] - param_1[param_3 + -1])) *
              (_DAT_10038ff8 / (param_1[param_3] - param_1[param_3 + -1]));
  }
  else {
    local_c = 0.0;
    local_10 = 0.0;
  }
  param_6[param_3] =
       (local_c - local_10 * pfVar4[param_3 + -1]) /
       (local_10 * param_6[param_3 + -1] + _DAT_10039000);
  iVar3 = param_3;
  while (local_18 = iVar3 + -1, 0 < local_18) {
    param_6[local_18] = param_6[local_18] * param_6[iVar3] + pfVar4[local_18];
    iVar3 = local_18;
  }
  free_vector(pfVar4,1,param_3 + -1);
  return;
}

//===== 0x10036302 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* void __cdecl splint(float const * const,float const * const,float const * const,int,float,float
   *) */

void __cdecl
splint(float *param_1,float *param_2,float *param_3,int param_4,float param_5,float *param_6)

{
  float fVar1;
  float fVar2;
  float fVar3;
  int iVar4;
  int iVar5;
  
                    /* 0x36302  408  ?splint@@YAXQBM00HMPAM@Z */
  if ((((DAT_10042748 == 0) || (DAT_10042764 == 0)) || (param_5 < param_1[DAT_10042748])) ||
     (param_1[DAT_10042764] < param_5)) {
    DAT_10042748 = 1;
    DAT_10042764 = param_4;
    iVar4 = DAT_10042748;
    while (DAT_10042748 = iVar4, 1 < DAT_10042764 - DAT_10042748) {
      iVar5 = DAT_10042764 + DAT_10042748 >> 1;
      iVar4 = iVar5;
      if (param_5 < param_1[iVar5]) {
        iVar4 = DAT_10042748;
        DAT_10042764 = iVar5;
      }
    }
  }
  fVar1 = param_1[DAT_10042764] - param_1[DAT_10042748];
  if (_DAT_10039008 == fVar1) {
    FUN_10033b80(s_Bad_xa_input_to_routine_splint__t_1004195c);
  }
  fVar2 = (param_1[DAT_10042764] - param_5) / fVar1;
  fVar3 = (param_5 - param_1[DAT_10042748]) / fVar1;
  *param_6 = (fVar1 * fVar1 *
             ((fVar3 * fVar3 * fVar3 - fVar3) * param_3[DAT_10042764] +
             (fVar2 * fVar2 * fVar2 - fVar2) * param_3[DAT_10042748])) / _DAT_10039004 +
             fVar3 * param_2[DAT_10042764] + fVar2 * param_2[DAT_10042748];
  return;
}

//===== 0x1003646e =====

void FUN_1003646e(void)

{
  FUN_10036478();
  return;
}

//===== 0x10036478 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_10036478(void)

{
  _DAT_100427b0 = acos(-1.0);
  return;
}

//===== 0x100364a0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void __cdecl FUN_100364a0(int param_1,int param_2,int param_3,int param_4)

{
  double dVar1;
  undefined4 local_44;
  undefined4 local_40;
  float local_3c;
  float local_38;
  int *local_34;
  int local_30;
  int local_2c;
  int local_28;
  float local_24;
  undefined4 local_20;
  int local_1c;
  int local_18;
  int *local_14;
  int local_10;
  int *local_c;
  int local_8;
  
  local_14 = ivector(1,param_2);
  local_c = ivector(1,param_2);
  local_34 = ivector(1,param_2);
  for (local_2c = 1; local_2c <= param_2; local_2c = local_2c + 1) {
    local_34[local_2c] = 0;
  }
  local_28 = 1;
  while( true ) {
    if (param_2 < local_28) {
      for (local_18 = param_2; 0 < local_18; local_18 = local_18 + -1) {
        if (local_c[local_18] != local_14[local_18]) {
          for (local_30 = 1; local_30 <= param_2; local_30 = local_30 + 1) {
            local_20 = *(undefined4 *)(*(int *)(param_1 + local_30 * 4) + local_c[local_18] * 4);
            *(undefined4 *)(*(int *)(param_1 + local_30 * 4) + local_c[local_18] * 4) =
                 *(undefined4 *)(*(int *)(param_1 + local_30 * 4) + local_14[local_18] * 4);
            *(undefined4 *)(*(int *)(param_1 + local_30 * 4) + local_14[local_18] * 4) = local_20;
          }
        }
      }
      free_ivector(local_34,1,param_2);
      free_ivector(local_c,1,param_2);
      free_ivector(local_14,1,param_2);
      return;
    }
    local_38 = 0.0;
    for (local_2c = 1; local_2c <= param_2; local_2c = local_2c + 1) {
      if (local_34[local_2c] != 1) {
        for (local_30 = 1; local_30 <= param_2; local_30 = local_30 + 1) {
          if (local_34[local_30] == 0) {
            dVar1 = fabs((double)*(float *)(*(int *)(param_1 + local_2c * 4) + local_30 * 4));
            if ((double)local_38 <= dVar1) {
              dVar1 = fabs((double)*(float *)(*(int *)(param_1 + local_2c * 4) + local_30 * 4));
              local_38 = (float)dVar1;
              local_1c = local_2c;
              local_10 = local_30;
            }
          }
          else if (1 < local_34[local_30]) {
            local_40 = 0;
                    /* WARNING: Subroutine does not return */
            _CxxThrowException(&local_40,(ThrowInfo *)&DAT_10039b88);
          }
        }
      }
    }
    local_34[local_10] = local_34[local_10] + 1;
    if (local_1c != local_10) {
      for (local_18 = 1; local_18 <= param_2; local_18 = local_18 + 1) {
        local_20 = *(undefined4 *)(*(int *)(param_1 + local_1c * 4) + local_18 * 4);
        *(undefined4 *)(*(int *)(param_1 + local_1c * 4) + local_18 * 4) =
             *(undefined4 *)(*(int *)(param_1 + local_10 * 4) + local_18 * 4);
        *(undefined4 *)(*(int *)(param_1 + local_10 * 4) + local_18 * 4) = local_20;
      }
      for (local_18 = 1; local_18 <= param_4; local_18 = local_18 + 1) {
        local_20 = *(undefined4 *)(*(int *)(param_3 + local_1c * 4) + local_18 * 4);
        *(undefined4 *)(*(int *)(param_3 + local_1c * 4) + local_18 * 4) =
             *(undefined4 *)(*(int *)(param_3 + local_10 * 4) + local_18 * 4);
        *(undefined4 *)(*(int *)(param_3 + local_10 * 4) + local_18 * 4) = local_20;
      }
    }
    local_c[local_28] = local_1c;
    local_14[local_28] = local_10;
    if (_DAT_1003900c == *(float *)(*(int *)(param_1 + local_10 * 4) + local_10 * 4)) break;
    local_24 = _DAT_10039010 / *(float *)(*(int *)(param_1 + local_10 * 4) + local_10 * 4);
    *(undefined4 *)(*(int *)(param_1 + local_10 * 4) + local_10 * 4) = 0x3f800000;
    for (local_18 = 1; local_18 <= param_2; local_18 = local_18 + 1) {
      *(float *)(*(int *)(param_1 + local_10 * 4) + local_18 * 4) =
           *(float *)(*(int *)(param_1 + local_10 * 4) + local_18 * 4) * local_24;
    }
    for (local_18 = 1; local_18 <= param_4; local_18 = local_18 + 1) {
      *(float *)(*(int *)(param_3 + local_10 * 4) + local_18 * 4) =
           *(float *)(*(int *)(param_3 + local_10 * 4) + local_18 * 4) * local_24;
    }
    for (local_8 = 1; local_8 <= param_2; local_8 = local_8 + 1) {
      if (local_8 != local_10) {
        local_3c = *(float *)(*(int *)(param_1 + local_8 * 4) + local_10 * 4);
        *(undefined4 *)(*(int *)(param_1 + local_8 * 4) + local_10 * 4) = 0;
        for (local_18 = 1; local_18 <= param_2; local_18 = local_18 + 1) {
          *(float *)(*(int *)(param_1 + local_8 * 4) + local_18 * 4) =
               *(float *)(*(int *)(param_1 + local_8 * 4) + local_18 * 4) -
               *(float *)(*(int *)(param_1 + local_10 * 4) + local_18 * 4) * local_3c;
        }
        for (local_18 = 1; local_18 <= param_4; local_18 = local_18 + 1) {
          *(float *)(*(int *)(param_3 + local_8 * 4) + local_18 * 4) =
               *(float *)(*(int *)(param_3 + local_8 * 4) + local_18 * 4) -
               *(float *)(*(int *)(param_3 + local_10 * 4) + local_18 * 4) * local_3c;
        }
      }
    }
    local_28 = local_28 + 1;
  }
  local_44 = 0;
                    /* WARNING: Subroutine does not return */
  _CxxThrowException(&local_44,(ThrowInfo *)&DAT_10039b78);
}

//===== 0x100369b0 =====

double __cdecl acos(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369b0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = acos(_X);
  return dVar1;
}

//===== 0x100369b6 =====

void __cdecl operator_delete(void *param_1)

{
                    /* WARNING: Could not recover jumptable at 0x100369b6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  operator_delete(param_1);
  return;
}

//===== 0x100369bc =====

void * __cdecl operator_new(uint param_1)

{
  void *pvVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369bc. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  pvVar1 = operator_new(param_1);
  return pvVar1;
}

//===== 0x100369c2 =====

double __cdecl sqrt(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369c2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = sqrt(_X);
  return dVar1;
}

//===== 0x100369c8 =====

void __cdecl ftol(void)

{
                    /* WARNING: Could not recover jumptable at 0x100369c8. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  ftol();
  return;
}

//===== 0x100369ce =====

double __cdecl cos(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369ce. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = cos(_X);
  return dVar1;
}

//===== 0x100369d4 =====

double __cdecl exp(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369d4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = exp(_X);
  return dVar1;
}

//===== 0x100369e0 =====

void * __cdecl memset(void *_Dst,int _Val,size_t _Size)

{
  void *pvVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369e0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  pvVar1 = memset(_Dst,_Val,_Size);
  return pvVar1;
}

//===== 0x100369e6 =====

void * __cdecl memcpy(void *_Dst,void *_Src,size_t _Size)

{
  void *pvVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369e6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  pvVar1 = memcpy(_Dst,_Src,_Size);
  return pvVar1;
}

//===== 0x100369ec =====

char * __cdecl strcpy(char *_Dest,char *_Source)

{
  char *pcVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369ec. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  pcVar1 = strcpy(_Dest,_Source);
  return pcVar1;
}

//===== 0x100369f2 =====

double __cdecl fmod(double _X,double _Y)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369f2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = fmod(_X,_Y);
  return dVar1;
}

//===== 0x100369f8 =====

double __cdecl fabs(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369f8. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = fabs(_X);
  return dVar1;
}

//===== 0x100369fe =====

double __cdecl log(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x100369fe. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = log(_X);
  return dVar1;
}

//===== 0x10036a04 =====

double __cdecl sin(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x10036a04. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = sin(_X);
  return dVar1;
}

//===== 0x10036a10 =====

void FUN_10036a10(undefined4 param_1,undefined4 param_2,int param_3,undefined *param_4)

{
  int iVar1;
  void *local_14;
  undefined *puStack_10;
  undefined *puStack_c;
  undefined4 local_8;
  
  puStack_c = &DAT_10039018;
  puStack_10 = &DAT_10036e4c;
  local_14 = ExceptionList;
  local_8 = 0;
  ExceptionList = &local_14;
  for (iVar1 = 0; iVar1 < param_3; iVar1 = iVar1 + 1) {
    (*(code *)param_4)();
  }
  local_8 = 0xffffffff;
  FUN_10036a88();
  ExceptionList = local_14;
  return;
}

//===== 0x10036a88 =====

void FUN_10036a88(void)

{
  undefined4 unaff_EBX;
  int unaff_EBP;
  int unaff_ESI;
  undefined4 unaff_EDI;
  
  if (*(int *)(unaff_EBP + -0x20) == 0) {
    FUN_10036b60(unaff_EDI,unaff_EBX,unaff_ESI,*(undefined **)(unaff_EBP + 0x18));
  }
  return;
}

//===== 0x10036ab0 =====

void FUN_10036ab0(undefined4 param_1,undefined4 param_2,int param_3,undefined *param_4)

{
  void *local_14;
  undefined *puStack_10;
  undefined *puStack_c;
  undefined4 local_8;
  
  puStack_c = &DAT_10039028;
  puStack_10 = &DAT_10036e4c;
  local_14 = ExceptionList;
  local_8 = 0;
  ExceptionList = &local_14;
  while( true ) {
    param_3 = param_3 + -1;
    if (param_3 < 0) break;
    (*(code *)param_4)();
  }
  local_8 = 0xffffffff;
  FUN_10036b29();
  ExceptionList = local_14;
  return;
}

//===== 0x10036b29 =====

void FUN_10036b29(void)

{
  int unaff_EBP;
  undefined4 unaff_ESI;
  undefined4 unaff_EDI;
  
  if (*(int *)(unaff_EBP + -0x1c) == 0) {
    FUN_10036b60(unaff_ESI,unaff_EDI,*(int *)(unaff_EBP + 0x10),*(undefined **)(unaff_EBP + 0x14));
  }
  return;
}

//===== 0x10036b60 =====

void FUN_10036b60(undefined4 param_1,undefined4 param_2,int param_3,undefined *param_4)

{
  void *local_14;
  undefined *puStack_10;
  undefined *puStack_c;
  undefined4 local_8;
  
  puStack_c = &DAT_10039038;
  puStack_10 = &DAT_10036e4c;
  local_14 = ExceptionList;
  local_8 = 0;
  ExceptionList = &local_14;
  while( true ) {
    param_3 = param_3 + -1;
    if (param_3 < 0) break;
    (*(code *)param_4)();
  }
  ExceptionList = local_14;
  return;
}

//===== 0x10036bf0 =====

int __cdecl abs(int _X)

{
  int iVar1;
  
                    /* WARNING: Could not recover jumptable at 0x10036bf0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  iVar1 = abs(_X);
  return iVar1;
}

//===== 0x10036c00 =====

/* WARNING: Unable to track spacebase fully for stack */

void FUN_10036c00(void)

{
  uint in_EAX;
  undefined1 *puVar1;
  undefined4 unaff_retaddr;
  
  puVar1 = &stack0x00000004;
  for (; 0xfff < in_EAX; in_EAX = in_EAX - 0x1000) {
    puVar1 = puVar1 + -0x1000;
  }
  *(undefined4 *)(puVar1 + (-4 - in_EAX)) = unaff_retaddr;
  return;
}

//===== 0x10036c30 =====

double __cdecl log10(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x10036c30. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = log10(_X);
  return dVar1;
}

//===== 0x10036c36 =====

size_t __cdecl strlen(char *_Str)

{
  size_t sVar1;
  
                    /* WARNING: Could not recover jumptable at 0x10036c36. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  sVar1 = strlen(_Str);
  return sVar1;
}

//===== 0x10036c3c =====

double __cdecl pow(double _X,double _Y)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x10036c3c. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = pow(_X,_Y);
  return dVar1;
}

//===== 0x10036c42 =====

double __cdecl atan(double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x10036c42. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = atan(_X);
  return dVar1;
}

//===== 0x10036c50 =====

void __cdecl FUN_10036c50(_onexit_t param_1)

{
  if (DAT_100427c8 == -1) {
    _onexit(param_1);
    return;
  }
  __dllonexit(param_1,&DAT_100427c8,&DAT_100427c4);
  return;
}

//===== 0x10036c80 =====

int __cdecl FUN_10036c80(_onexit_t param_1)

{
  int iVar1;
  
  iVar1 = FUN_10036c50(param_1);
  return (iVar1 != 0) - 1;
}

//===== 0x10036ca0 =====

type_info * __thiscall FUN_10036ca0(void *this,byte param_1)

{
  type_info::~type_info(this);
  if ((param_1 & 1) != 0) {
    operator_delete(this);
  }
  return this;
}

//===== 0x10036cc0 =====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_10036cc0(undefined4 param_1,int param_2)

{
  undefined4 *_Memory;
  undefined4 *puVar1;
  
  if (param_2 == 0) {
    if (DAT_100427b8 < 1) {
      return 0;
    }
    DAT_100427b8 = DAT_100427b8 + -1;
  }
  _DAT_100427bc = *(undefined4 *)_adjust_fdiv_exref;
  if (param_2 == 1) {
    DAT_100427c8 = malloc(0x80);
    if (DAT_100427c8 == (undefined4 *)0x0) {
      return 0;
    }
    *DAT_100427c8 = 0;
    DAT_100427c4 = DAT_100427c8;
    initterm(&DAT_1003f000,&DAT_1003f090);
    DAT_100427b8 = DAT_100427b8 + 1;
    return 1;
  }
  if ((param_2 == 0) && (DAT_100427c8 != (undefined4 *)0x0)) {
    puVar1 = DAT_100427c4 + -1;
    _Memory = DAT_100427c8;
    if (DAT_100427c8 <= puVar1) {
      do {
        if ((code *)*puVar1 != (code *)0x0) {
          (*(code *)*puVar1)();
          _Memory = DAT_100427c8;
        }
        puVar1 = puVar1 + -1;
      } while (_Memory <= puVar1);
    }
    free(_Memory);
    DAT_100427c8 = (undefined4 *)0x0;
  }
  return 1;
}

//===== 0x10036d90 =====

int entry(HMODULE param_1,int param_2,undefined4 param_3)

{
  int iVar1;
  int iVar2;
  
  iVar1 = 1;
  if ((param_2 == 0) && (DAT_100427b8 == 0)) {
    return 0;
  }
  if ((param_2 != 1) && (param_2 != 2)) {
LAB_10036dee:
    iVar1 = FUN_10036e70(param_1,param_2);
    if ((param_2 == 1) && (iVar1 == 0)) {
      FUN_10036cc0(param_1,0);
    }
    if ((param_2 == 0) || (param_2 == 3)) {
      iVar2 = FUN_10036cc0(param_1,param_2);
      if (iVar2 == 0) {
        iVar1 = 0;
      }
      if ((iVar1 != 0) && (DAT_100427c0 != (code *)0x0)) {
        iVar1 = (*DAT_100427c0)(param_1,param_2,param_3);
      }
    }
    return iVar1;
  }
  if (DAT_100427c0 != (code *)0x0) {
    iVar1 = (*DAT_100427c0)(param_1,param_2,param_3);
  }
  if (iVar1 != 0) {
    iVar1 = FUN_10036cc0(param_1,param_2);
    if (iVar1 != 0) goto LAB_10036dee;
  }
  return 0;
}

//===== 0x10036e40 =====

double __cdecl atan2(double _Y,double _X)

{
  double dVar1;
  
                    /* WARNING: Could not recover jumptable at 0x10036e40. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  dVar1 = atan2(_Y,_X);
  return dVar1;
}

//===== 0x10036e46 =====

void _CxxThrowException(void *pExceptionObject,ThrowInfo *pThrowInfo)

{
                    /* WARNING: Could not recover jumptable at 0x10036e46. Too many branches */
                    /* WARNING: Subroutine does not return */
                    /* WARNING: Treating indirect jump as call */
  _CxxThrowException(pExceptionObject,pThrowInfo);
  return;
}

//===== 0x10036e58 =====

void __dllonexit(void)

{
                    /* WARNING: Could not recover jumptable at 0x10036e58. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  __dllonexit();
  return;
}

//===== 0x10036e5e =====

void __thiscall type_info::~type_info(type_info *this)

{
                    /* WARNING: Could not recover jumptable at 0x10036e5e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  ~type_info(this);
  return;
}

//===== 0x10036e64 =====

void __cdecl initterm(void)

{
                    /* WARNING: Could not recover jumptable at 0x10036e64. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  initterm();
  return;
}

//===== 0x10036e70 =====

undefined4 FUN_10036e70(HMODULE param_1,int param_2)

{
  if ((param_2 == 1) && (DAT_100427c0 == 0)) {
    DisableThreadLibraryCalls(param_1);
  }
  return 1;
}

//===== 0x10036ea0 =====

void Unwind_10036ea0(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x28));
  return;
}

//===== 0x10036ec0 =====

void Unwind_10036ec0(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x40));
  return;
}

//===== 0x10036ed5 =====

void Unwind_10036ed5(void)

{
  int unaff_EBP;
  
  AboutBQ::~AboutBQ((AboutBQ *)(unaff_EBP + -0x10));
  return;
}

//===== 0x10036ee8 =====

void Unwind_10036ee8(void)

{
  int unaff_EBP;
  
  AboutBQ::~AboutBQ((AboutBQ *)(unaff_EBP + -0x10));
  return;
}

//===== 0x10036efb =====

void Unwind_10036efb(void)

{
  int unaff_EBP;
  
  AboutBQ::~AboutBQ((AboutBQ *)(unaff_EBP + -0x10));
  return;
}

//===== 0x10036f10 =====

void Unwind_10036f10(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x18) + 0xd0));
  return;
}

//===== 0x10036f29 =====

void Unwind_10036f29(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x10) + 0xd0));
  return;
}

//===== 0x10036f38 =====

void Unwind_10036f38(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x10) + 0x3d8));
  return;
}

//===== 0x10036f51 =====

void Unwind_10036f51(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x10) + 0xd0));
  return;
}

//===== 0x10036f60 =====

void Unwind_10036f60(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x10) + 0x3d8));
  return;
}

//===== 0x10036f79 =====

void Unwind_10036f79(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x1c));
  return;
}

//===== 0x10036f8e =====

void Unwind_10036f8e(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x18));
  return;
}

//===== 0x10036fb0 =====

void Unwind_10036fb0(void)

{
  int unaff_EBP;
  
  ObsInpSpec::~ObsInpSpec((ObsInpSpec *)(unaff_EBP + -0xf4));
  return;
}

//===== 0x10036fd0 =====

void Unwind_10036fd0(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x1c));
  return;
}

//===== 0x10036fe5 =====

void Unwind_10036fe5(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x30));
  return;
}

//===== 0x10037000 =====

void Unwind_10037000(void)

{
  int unaff_EBP;
  
  FUN_10024a62(unaff_EBP + -0xa84c);
  return;
}

//===== 0x10037020 =====

void Unwind_10037020(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0xbc));
  return;
}

//===== 0x1003702e =====

void Unwind_1003702e(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0xc4));
  return;
}

//===== 0x1003703c =====

void Unwind_1003703c(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0xe4));
  return;
}

//===== 0x1003704a =====

void Unwind_1003704a(void)

{
  int unaff_EBP;
  
  Mobility::~Mobility((Mobility *)(unaff_EBP + -0xb8));
  return;
}

//===== 0x10037060 =====

void Unwind_10037060(void)

{
  int unaff_EBP;
  
  FUN_1001dece(unaff_EBP + -0x84);
  return;
}

//===== 0x1003706c =====

void Unwind_1003706c(void)

{
  int unaff_EBP;
  
  FUN_1001dece(unaff_EBP + -0x5c);
  return;
}

//===== 0x10037075 =====

void Unwind_10037075(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x108));
  return;
}

//===== 0x10037090 =====

void Unwind_10037090(void)

{
  int unaff_EBP;
  
  if ((*(uint *)(unaff_EBP + -0x24) & 1) != 0) {
    BandStat::~BandStat(*(BandStat **)(unaff_EBP + 8));
  }
  return;
}

//===== 0x100370c0 =====

void Unwind_100370c0(void)

{
  int unaff_EBP;
  
  LMConvert::~LMConvert((LMConvert *)(unaff_EBP + -0x70));
  return;
}

//===== 0x100370c9 =====

void Unwind_100370c9(void)

{
  int unaff_EBP;
  
  LMConvert::~LMConvert((LMConvert *)(unaff_EBP + -0x9c));
  return;
}

//===== 0x100370e0 =====

void Unwind_100370e0(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x40));
  return;
}

//===== 0x100370e9 =====

void Unwind_100370e9(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x2c));
  return;
}

//===== 0x10037100 =====

void Unwind_10037100(void)

{
  int unaff_EBP;
  
  LMConvert::~LMConvert((LMConvert *)(unaff_EBP + -0xa4));
  return;
}

//===== 0x10037120 =====

void Unwind_10037120(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(*(int *)(unaff_EBP + -0x10) + 0xcc));
  return;
}

//===== 0x10037139 =====

void Unwind_10037139(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(*(int *)(unaff_EBP + -0x14) + 0xcc));
  return;
}

//===== 0x10037152 =====

void Unwind_10037152(void)

{
  int unaff_EBP;
  
  BandStatArray::~BandStatArray((BandStatArray *)(*(int *)(unaff_EBP + -0x14) + 0x1c));
  return;
}

//===== 0x1003715e =====

void Unwind_1003715e(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x14) + 0x28));
  return;
}

//===== 0x10037174 =====

void Unwind_10037174(void)

{
  int unaff_EBP;
  
  BandStatArray::~BandStatArray((BandStatArray *)(*(int *)(unaff_EBP + -0x14) + 0x1c));
  return;
}

//===== 0x10037180 =====

void Unwind_10037180(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x14) + 0x28));
  return;
}

//===== 0x1003718c =====

void Unwind_1003718c(void)

{
  int unaff_EBP;
  
  QualCtrl::~QualCtrl((QualCtrl *)(*(int *)(unaff_EBP + -0x14) + 0x330));
  return;
}

//===== 0x100371a5 =====

void Unwind_100371a5(void)

{
  int unaff_EBP;
  
  BandStatArray::~BandStatArray((BandStatArray *)(*(int *)(unaff_EBP + -0x10) + 0x1c));
  return;
}

//===== 0x100371b1 =====

void Unwind_100371b1(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(*(int *)(unaff_EBP + -0x10) + 0x28));
  return;
}

//===== 0x100371bd =====

void Unwind_100371bd(void)

{
  int unaff_EBP;
  
  QualCtrl::~QualCtrl((QualCtrl *)(*(int *)(unaff_EBP + -0x10) + 0x330));
  return;
}

//===== 0x100371d6 =====

void Unwind_100371d6(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x34));
  return;
}

//===== 0x100371df =====

void Unwind_100371df(void)

{
  int unaff_EBP;
  
  SW::~SW((SW *)(unaff_EBP + -0x8c));
  return;
}

//===== 0x10037200 =====

void Unwind_10037200(void)

{
  int unaff_EBP;
  
  LMConvert::~LMConvert((LMConvert *)(unaff_EBP + -0x80));
  return;
}

//===== 0x10037209 =====

void Unwind_10037209(void)

{
  int unaff_EBP;
  
  LMConvert::~LMConvert((LMConvert *)(unaff_EBP + -0x5c));
  return;
}

//===== 0x10037212 =====

void Unwind_10037212(void)

{
  int unaff_EBP;
  
  LMConvert::~LMConvert((LMConvert *)(unaff_EBP + -200));
  return;
}

//===== 0x1003721e =====

void Unwind_1003721e(void)

{
  int unaff_EBP;
  
  LMConvert::~LMConvert((LMConvert *)(unaff_EBP + -0xa4));
  return;
}

//===== 0x10037240 =====

void Unwind_10037240(void)

{
  int unaff_EBP;
  
  BandStatArray::~BandStatArray((BandStatArray *)(*(int *)(unaff_EBP + -0x10) + 0x14));
  return;
}

//===== 0x1003724c =====

void Unwind_1003724c(void)

{
  int unaff_EBP;
  
  FUN_10036ab0(*(int *)(unaff_EBP + -0x10) + 0x1c,0x14,0x800,BandStat::~BandStat);
  return;
}

//===== 0x1003726f =====

void Unwind_1003726f(void)

{
  int unaff_EBP;
  
  BandStatArray::~BandStatArray((BandStatArray *)(*(int *)(unaff_EBP + -0x18) + 0x14));
  return;
}

//===== 0x1003727b =====

void Unwind_1003727b(void)

{
  int unaff_EBP;
  
  FUN_10036ab0(*(int *)(unaff_EBP + -0x18) + 0x1c,0x14,0x800,BandStat::~BandStat);
  return;
}

//===== 0x10037294 =====

void Unwind_10037294(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x10));
  return;
}

//===== 0x100372a9 =====

void Unwind_100372a9(void)

{
  int unaff_EBP;
  
  BandStatArray::~BandStatArray((BandStatArray *)(*(int *)(unaff_EBP + -0x20) + 0x14));
  return;
}

//===== 0x100372b5 =====

void Unwind_100372b5(void)

{
  int unaff_EBP;
  
  FUN_10036ab0(*(int *)(unaff_EBP + -0x20) + 0x1c,0x14,0x800,BandStat::~BandStat);
  return;
}

//===== 0x100372d8 =====

void Unwind_100372d8(void)

{
  int unaff_EBP;
  
  BandStatArray::~BandStatArray((BandStatArray *)(*(int *)(unaff_EBP + -0x10) + 0x14));
  return;
}

//===== 0x100372e4 =====

void Unwind_100372e4(void)

{
  int unaff_EBP;
  
  FUN_10036ab0(*(int *)(unaff_EBP + -0x10) + 0x1c,0x14,0x800,BandStat::~BandStat);
  return;
}

//===== 0x10037307 =====

void Unwind_10037307(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x20));
  return;
}

//===== 0x10037312 =====

void Unwind_10037312(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x28));
  return;
}

//===== 0x10037327 =====

void Unwind_10037327(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x18));
  return;
}

//===== 0x10037340 =====

void Unwind_10037340(void)

{
  int unaff_EBP;
  
  FUN_100273ca(unaff_EBP + -0x24);
  return;
}

//===== 0x10037353 =====

void Unwind_10037353(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x14));
  return;
}

//===== 0x1003735c =====

void Unwind_1003735c(void)

{
  int unaff_EBP;
  
  if ((*(uint *)(unaff_EBP + -0x18) & 1) != 0) {
    BandStat::~BandStat(*(BandStat **)(unaff_EBP + 8));
  }
  return;
}

//===== 0x1003737d =====

void Unwind_1003737d(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x34));
  return;
}

//===== 0x10037392 =====

void Unwind_10037392(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x18));
  return;
}

//===== 0x1003739b =====

void Unwind_1003739b(void)

{
  int unaff_EBP;
  
  if ((*(uint *)(unaff_EBP + -0x1c) & 1) != 0) {
    BandStat::~BandStat(*(BandStat **)(unaff_EBP + 8));
  }
  return;
}

//===== 0x100373bc =====

void Unwind_100373bc(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x18));
  return;
}

//===== 0x100373c7 =====

void Unwind_100373c7(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x20));
  return;
}

//===== 0x100373dc =====

void Unwind_100373dc(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x18));
  return;
}

//===== 0x100373e5 =====

void Unwind_100373e5(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x2c));
  return;
}

//===== 0x100373f0 =====

void Unwind_100373f0(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x34));
  return;
}

//===== 0x100373fb =====

void Unwind_100373fb(void)

{
  int unaff_EBP;
  
  BandStat::~BandStat((BandStat *)(unaff_EBP + -0x40));
  return;
}

//===== 0x1003740e =====

void Unwind_1003740e(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x28));
  return;
}

//===== 0x10037419 =====

void Unwind_10037419(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x30));
  return;
}

//===== 0x1003742e =====

void Unwind_1003742e(void)

{
  int unaff_EBP;
  
  FUN_100273ca(unaff_EBP + -0x28);
  return;
}

//===== 0x1003745a =====

void Unwind_1003745a(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x78));
  return;
}

//===== 0x10037465 =====

void Unwind_10037465(void)

{
  int unaff_EBP;
  
  FUN_10013cdd(unaff_EBP + -0x68);
  return;
}

//===== 0x10037490 =====

void Unwind_10037490(void)

{
  int unaff_EBP;
  
  Annotate::~Annotate((Annotate *)(*(int *)(unaff_EBP + -0x18) + 4));
  return;
}

//===== 0x100374a6 =====

void Unwind_100374a6(void)

{
  int unaff_EBP;
  
  Annotate::~Annotate((Annotate *)(*(int *)(unaff_EBP + -0x168) + 4));
  return;
}

//===== 0x100374b5 =====

void Unwind_100374b5(void)

{
  int unaff_EBP;
  
  ObsInpSpec::~ObsInpSpec((ObsInpSpec *)(*(int *)(unaff_EBP + -0x168) + 0x210));
  return;
}

//===== 0x100374d1 =====

void Unwind_100374d1(void)

{
  int unaff_EBP;
  
  Annotate::~Annotate((Annotate *)(*(int *)(unaff_EBP + -0x24) + 4));
  return;
}

//===== 0x100374dd =====

void Unwind_100374dd(void)

{
  int unaff_EBP;
  
  ObsInpSpec::~ObsInpSpec((ObsInpSpec *)(*(int *)(unaff_EBP + -0x24) + 0x210));
  return;
}

//===== 0x100374f6 =====

void Unwind_100374f6(void)

{
  int unaff_EBP;
  
  Annotate::~Annotate((Annotate *)(*(int *)(unaff_EBP + -0x18) + 4));
  return;
}

//===== 0x10037502 =====

void Unwind_10037502(void)

{
  int unaff_EBP;
  
  ObsInpSpec::~ObsInpSpec((ObsInpSpec *)(*(int *)(unaff_EBP + -0x18) + 0x210));
  return;
}

//===== 0x1003751b =====

void Unwind_1003751b(void)

{
  int unaff_EBP;
  
  Annotate::~Annotate((Annotate *)(*(int *)(unaff_EBP + -0x10) + 4));
  return;
}

//===== 0x10037527 =====

void Unwind_10037527(void)

{
  int unaff_EBP;
  
  ObsInpSpec::~ObsInpSpec((ObsInpSpec *)(*(int *)(unaff_EBP + -0x10) + 0x210));
  return;
}

//===== 0x10037540 =====

void Unwind_10037540(void)

{
  int unaff_EBP;
  
  FUN_10009624(unaff_EBP + -0x388);
  return;
}

//===== 0x10037556 =====

void Unwind_10037556(void)

{
  int unaff_EBP;
  
  FUN_100285a5(unaff_EBP + -0x4b8);
  return;
}

//===== 0x10037562 =====

void Unwind_10037562(void)

{
  int unaff_EBP;
  
  FUN_10013cdd(unaff_EBP + -0x4c);
  return;
}

//===== 0x10037575 =====

void Unwind_10037575(void)

{
  int unaff_EBP;
  
  Wvfm::~Wvfm((Wvfm *)(unaff_EBP + -0x318));
  return;
}

//===== 0x10037590 =====

void Unwind_10037590(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x6c));
  return;
}

//===== 0x1003759b =====

void Unwind_1003759b(void)

{
  int unaff_EBP;
  
  operator_delete(*(void **)(unaff_EBP + -0x74));
  return;
}

