// Copyright (C) 2026 Gabriel Russo
// Copyright (C) 2023 Anthony <https://github.com/aholinch>
// See end of file for extended copyright information.

#ifndef __sgp4tleheader__
#define __sgp4tleheader__

#include "SGP4.h"

typedef struct TLE
{
    ElsetRec rec;
    char line1[70];
    char line2[70];
    char intlid[12];
    char objectID[6];
    long epoch;
    double ndot;
    double nddot;
    double bstar;
    int elnum;
    double incDeg;
    double raanDeg;
    double ecc;
    double argpDeg;
    double maDeg;
    double n;
    int revnum;
    int sgp4Error;
} TLE;

void parseLines(TLE *tle, char *line1, char *line2);

long parseEpoch(ElsetRec *rec, char *str);

void getRVForDate(TLE *tle, long millisSince1970, double r[3], double v[3]);

void getRV(TLE *tle, double minutesAfterEpoch, double r[3], double v[3]);

/*     ----------------------------------------------------------------
 *
 *                               Fork
 *  Get Satellite position on Datum WGS84.
 *
 *  Author: Gabriel Russo
 *
 *  11 fev 26
 *
/* --------------------------------------------------------------------- */

#define WGS84_A 6378.137
#define WGS84_F (1.0 / 298.257223563)
#define WGS84_E2 (2 * WGS84_F - WGS84_F * WGS84_F)

typedef struct Position
{
    double latitude;
    double longitude;
    double altitude;
} Position;

long isoToMillis(char *iso);

void temeToGeodetic(double r[3], long millis, double *lat, double *lon, double *alt);

Position satellite_geographic_position(char line1[], char line2[], char at[]);

#endif

// MIT License
//
// Copyright (C) 2026 Gabriel Russo
// Copyright (C) 2023 Anthony <https://github.com/aholinch>
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
