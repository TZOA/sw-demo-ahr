/********************************************************************************************************************//*
 * @file      AhrDemo.cpp
 * @author    Colin E. Fitzgerald
 * @copyright Copyright © 2020 Clad Innovations Ltd.  All rights reserved.
 **********************************************************************************************************************/
#include "AhrDemo.h"

// System/Framework include's
#include <QDebug>
#include <QLowEnergyCharacteristic>
#include <QTimer>


AhrDemo::AhrDemo(QObject *parent) : QObject(parent) {
  bleController_ = nullptr;
  bleService_ = nullptr;
} // AhrDemo()


void AhrDemo::run(void) {

  bleDiscoveryAgent_.setInquiryType(QBluetoothDeviceDiscoveryAgent::GeneralUnlimitedInquiry);
  bleDiscoveryAgent_.setLowEnergyDiscoveryTimeout(5000);

  connect(&bleDiscoveryAgent_, SIGNAL(deviceDiscovered(QBluetoothDeviceInfo)), this, SLOT(bleDeviceDiscovered(QBluetoothDeviceInfo)));
  connect(&bleDiscoveryAgent_, SIGNAL(finished()), this, SLOT(bleDeviceDiscoveryFinished()));

  bleDiscoveryAgent_.start(QBluetoothDeviceDiscoveryAgent::LowEnergyMethod);

} // run()


void AhrDemo::bleDeviceDiscovered(const QBluetoothDeviceInfo &info) {
  if (info.name() != "HAVEN-CAC-1939-0004")
    return;

  //bleDiscoveryAgent_.stop();

  info_ = info;
} // bleDeviceDiscovered()


void AhrDemo::bleDeviceDiscoveryFinished(void) {
  qDebug() << "BLE device discovery finished.";

  bleController_ = QLowEnergyController::createCentral(info_, this);

  connect(bleController_, SIGNAL(connected()), this, SLOT(bleDeviceConnected()));
  connect(bleController_, SIGNAL(disconnected()), this, SLOT(bleDeviceDisconnected()));
  connect(bleController_, SIGNAL(error(QLowEnergyController::Error)), this, SLOT(bleDeviceError(QLowEnergyController::Error)));
  connect(bleController_, SIGNAL(serviceDiscovered(const QBluetoothUuid &)), this, SLOT(bleServiceDiscovered(const QBluetoothUuid &)));
  connect(bleController_, SIGNAL(discoveryFinished()), this, SLOT(bleServiceDiscoveryFinished()));

  qDebug() << info_.name() << info_.address() << info_.rssi();

  bleController_->connectToDevice();

} // bleDeviceDiscoveryFinished()


void AhrDemo::bleDeviceConnected(void) {
  qDebug() << "BLE device connected.";

  bleController_->discoverServices();
  //bleController_->disconnectFromDevice();
} // bleDeviceConnected()


void AhrDemo::bleDeviceDisconnected(void) {
  qDebug() << "BLE device disconnected.";

  bleController_->deleteLater();
  bleService_->deleteLater();

  bleController_ = nullptr;
  bleService_ = nullptr;

  emit finished();
} // bleDeviceDisconnected()


void AhrDemo::bleDeviceError(QLowEnergyController::Error error) {
  qDebug() << "BLE device error:" << error;
} // bleDeviceError()

void AhrDemo::bleServiceDiscovered(const QBluetoothUuid &service) {
  qDebug() << "BLE service discovered: " << service.toString();

  //if (service != QUuid("0000A216-0000-1000-8000-00805F9B34FB"))
  if (service != QUuid("0000a216-0000-1000-8000-00805f9b34fb"))
    return;

  qDebug() << "Target BLE service found.";

  service_ = service;
} // bleServiceDiscovered()


void AhrDemo::bleServiceDiscoveryFinished(void) {
  qDebug() << "BLE service discovery finished.";

  bleService_ = bleController_->createServiceObject(service_, this);

  connect(bleService_, SIGNAL(stateChanged(QLowEnergyService::ServiceState)), this, SLOT(bleServiceStateChanged(QLowEnergyService::ServiceState)));

  bleService_->discoverDetails();

  QTimer::singleShot(5000, this, SLOT(temp()));
} // bleServiceDiscoveryFinished()


void AhrDemo::bleServiceStateChanged(QLowEnergyService::ServiceState state) {
  qDebug() << "BLE service state changed:" << state;

} // bleServiceStateChanged()


void AhrDemo::temp(void) {
  QLowEnergyCharacteristic c = bleService_->characteristic(QBluetoothUuid(QUuid("0000FF04-0000-1000-8000-00805F9B34FB")));

  qDebug() << c.isValid();

  /*
  qDebug() << bleService_->characteristics().length();

  foreach (QLowEnergyCharacteristic c, bleService_->characteristics()) {
    qDebug() << c.name();
  }
  */
} // XXXX()

// End of file.
