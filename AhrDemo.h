/********************************************************************************************************************//*
 * @file      AhrDemo.h
 * @author    Colin E. Fitzgerald
 * @copyright Copyright © 2020 Clad Innovations Ltd.  All rights reserved.
 **********************************************************************************************************************/
#ifndef AHRDEMO_H
#define AHRDEMO_H

// System/Framework include's
#include <QObject>
#include <QBluetoothDeviceDiscoveryAgent>
#include <QBluetoothDeviceInfo>
#include <QLowEnergyController>
#include <QLowEnergyService>

// Project include's


class AhrDemo : public QObject {
  Q_OBJECT

  public:
    AhrDemo(QObject *parent = nullptr);

  public slots:
    void run(void);

    void bleDeviceDiscovered(const QBluetoothDeviceInfo &info);
    void bleDeviceDiscoveryFinished(void);
    void bleDeviceConnected(void);
    void bleDeviceDisconnected(void);
    void bleDeviceError(QLowEnergyController::Error);
    void bleServiceDiscovered(const QBluetoothUuid &service);
    void bleServiceDiscoveryFinished(void);
    void bleServiceStateChanged(QLowEnergyService::ServiceState state);
    void temp(void);

  signals:
    void finished(void);

  private:
    QBluetoothDeviceDiscoveryAgent bleDiscoveryAgent_;
    QLowEnergyController *bleController_;
    QLowEnergyService *bleService_;
    QBluetoothDeviceInfo info_;
    QBluetoothUuid service_;
}; // AhrDemo

#endif // AHRDEMO_H

// End of file.
